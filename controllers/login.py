from datetime import datetime, timedelta
import json
import logging
import os
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from fastapi import Request
import jwt

from datamodels import UserInfo
from db_connection_params_handler import ConnectionParamsHandler
from db_handlers.ibm_db2.db_query_manager import DatabaseManager
from db_handlers.ibm_db2.login_db_access import LoginDBAccess
from db_handlers.ibm_db2.user_db_access import UserDBAccess
from mappers.logininfo_mapper import LoginInfoMapper
from mappers.user_mapper import UserMapper

logger = logging.getLogger(__name__)


class SecretKeyStorage:
    def __init__(self):
        self.storage_path = Path(
            os.getenv(
                "JWT_SECRET_STORAGE_DIR",
                os.path.join(os.path.expanduser("~"), ".analysis_dashboard", "secrets"),
            )
        )

    def store_secret_key(self, key):
        self.storage_path.mkdir(parents=True, exist_ok=True)
        secret_file = self.storage_path / "secret_key.json"
        secret_file.write_text(json.dumps({"key": key}))
        secret_file.chmod(0o600)

    def retrieve_secret_key(self):
        env_secret = os.getenv("JWT_SECRET")
        if env_secret:
            return env_secret

        secret_file = self.storage_path / "secret_key.json"
        if not secret_file.exists():
            return None
        secret_data = json.loads(secret_file.read_text())
        return secret_data.get("key")


class TokenGenerator:
    def __init__(self, secret_key_storage: SecretKeyStorage, expiration_file_path: Optional[str] = None):
        self.secret_key_storage = secret_key_storage
        self.expiration_file_path = Path(
            expiration_file_path
            or os.getenv(
                "JWT_SECRET_EXPIRATION_FILE",
                os.path.join(os.path.expanduser("~"), ".analysis_dashboard", "expiration_date.txt"),
            )
        )
        self.expiration_time_day = int(os.getenv("JWT_SECRET_ROTATION_DAYS", "30"))

    def generate_secret_key(self):
        return Fernet.generate_key().decode()

    def store_secret_key(self, key):
        self.secret_key_storage.store_secret_key(key)

    def retrieve_secret_key(self):
        key = self.secret_key_storage.retrieve_secret_key()
        if key is None:
            key = self.generate_secret_key()
            self.secret_key_storage.store_secret_key(key)
        return key.encode()

    def generate_jwt_email_token(self, email, expiration_hours: int) -> str:
        secret_key = self.retrieve_secret_key()
        now = datetime.utcnow()
        payload = {
            "iat": int(now.timestamp()),
            "isLoggedIn": True,
            "exp": int((now + timedelta(hours=expiration_hours)).timestamp()),
            "email": email,
        }
        return jwt.encode(payload, secret_key, algorithm="HS256")

    def rotate_secret_key(self):
        # If JWT_SECRET is supplied by the environment, rotation is managed outside the app.
        if os.getenv("JWT_SECRET"):
            return

        current_date = datetime.utcnow()
        expiration_date = current_date + timedelta(days=self.expiration_time_day)

        if self.expiration_file_path.exists():
            expiration_date_str = self.expiration_file_path.read_text().strip()
            if expiration_date_str:
                expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d")

        if current_date > expiration_date:
            self.store_secret_key(self.generate_secret_key())
            expiration_date = current_date + timedelta(days=self.expiration_time_day)

        self.expiration_file_path.parent.mkdir(parents=True, exist_ok=True)
        self.expiration_file_path.write_text(expiration_date.strftime("%Y-%m-%d"))
        self.expiration_file_path.chmod(0o600)


def _extract_bearer_token(sent_token: Optional[str]) -> Optional[str]:
    if not sent_token:
        return None
    parts = sent_token.strip().split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return sent_token.strip()


def _token_generator() -> TokenGenerator:
    return TokenGenerator(SecretKeyStorage())


def generate_token(email) -> str:
    token_generator = _token_generator()
    token_generator.rotate_secret_key()
    expiration_hours = int(os.getenv("JWT_EXPIRATION_HOURS", "1"))
    return token_generator.generate_jwt_email_token(email, expiration_hours=expiration_hours)


def check_token_valid(sent_token: str) -> bool:
    token = _extract_bearer_token(sent_token)
    if not token:
        return False

    key = _token_generator().retrieve_secret_key()
    try:
        jwt.decode(token, key, algorithms=["HS256"])
        return True
    except jwt.ExpiredSignatureError:
        logger.info("JWT signature expired")
        return False
    except jwt.InvalidTokenError:
        logger.info("Invalid JWT token")
        return False


def decode_email_from_token(token: str) -> str:
    raw_token = _extract_bearer_token(token)
    key = _token_generator().retrieve_secret_key()
    decoded = jwt.decode(raw_token, key, algorithms=["HS256"])
    return decoded["email"]


def _database_manager_from_connection(connection: ConnectionParamsHandler) -> DatabaseManager:
    return DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )


def do_login(connection: ConnectionParamsHandler, email: str, password: str):
    db_manager = _database_manager_from_connection(connection)
    login_manager = LoginDBAccess(manager=db_manager)
    login_mapper = LoginInfoMapper(
        df=login_manager.get_connection_info_by_email_password(email, password)
    )
    try:
        login_info = login_mapper.generate_login_infos()[0]
    except (IndexError, KeyError):
        return None, None

    connection_params = login_info.update_connection_params_handler(connection)
    db_manager = _database_manager_from_connection(connection_params)
    user_manager = UserDBAccess(manager=db_manager)
    user_mapper = UserMapper(df_chunk_generator=user_manager.get_user_by_codcf(login_info.codcf))

    try:
        user: UserInfo = next(user_mapper.generate_users())
    except StopIteration:
        return None, None

    token = generate_token(email)
    user.email = login_info.user_mail

    return user.as_dict(), token


def retrieve_connection_params(
    request: Request, connection: ConnectionParamsHandler
) -> ConnectionParamsHandler:
    if os.getenv("DEV_BYPASS_LOGIN", "false").lower() == "true":
        config_file = os.getenv("ANALYSIS_DASHBOARD_CONFIG", "config.yml")
        try:
            dev_conn = ConnectionParamsHandler(
                connection_filename=config_file, section="database_user"
            )
            return dev_conn
        except Exception:
            return connection

    sent_token = request.headers.get("Authorization")
    if not check_token_valid(sent_token=sent_token):
        raise Exception("Invalid credentials")

    email = decode_email_from_token(sent_token)
    db_manager = _database_manager_from_connection(connection)
    login_manager = LoginDBAccess(manager=db_manager)
    login_mapper = LoginInfoMapper(df=login_manager.get_connection_info_by_email(email=email))
    try:
        login_info = login_mapper.generate_login_infos()[0]
    except IndexError:
        raise Exception("Invalid credentials")
    return login_info.update_connection_params_handler(connection)
