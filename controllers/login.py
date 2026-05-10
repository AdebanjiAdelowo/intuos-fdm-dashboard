from datetime import datetime, timedelta
import json
import os
from fastapi import Request
import jwt

from datamodels import UserInfo
from db_connection_params_handler import ConnectionParamsHandler
from db_handlers.ibm_db2.db_query_manager import DatabaseManager
from db_handlers.ibm_db2.login_db_access import LoginDBAccess
from db_handlers.ibm_db2.user_db_access import UserDBAccess
from mappers.logininfo_mapper import LoginInfoMapper
from mappers.user_mapper import UserMapper
from cryptography.fernet import Fernet


class SecretKeyStorage:
    def __init__(self):
        # Initialize the secret key storage mechanism
        # Example:
        # self.secret_key = retrieve_secret_key_from_aws_secrets_manager()
        self.storage_path = os.path.join(os.path.expanduser("~"), ".secret_key_storage")

    def store_secret_key(self, key):
        # Store the secret key locally
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)
        secret_data = {"key": key}
        with open(os.path.join(self.storage_path, "secret_key.json"), "w") as file:
            json.dump(secret_data, file)

    def retrieve_secret_key(self):
        # Retrieve the secret key from local storage
        if not os.path.exists(self.storage_path):
            return None
        with open(os.path.join(self.storage_path, "secret_key.json"), "r") as file:
            secret_data = json.load(file)
        return secret_data.get("key")


class TokenGenerator:
    def __init__(self, secret_key_storage: SecretKeyStorage, expiration_file_path: str):
        self.secret_key_storage = secret_key_storage
        self.expiration_file_path = expiration_file_path
        self.expiration_time_day = 30

    def generate_secret_key(self):
        key_encoded = Fernet.generate_key()
        key = key_encoded.decode()
        return key

    def store_secret_key(self, key):
        self.secret_key_storage.store_secret_key(key)

    def retrieve_secret_key(self):
        if self.secret_key_storage.retrieve_secret_key() is None:
            self.secret_key_storage.store_secret_key(self.generate_secret_key())
        return self.secret_key_storage.retrieve_secret_key().encode()

    def generate_jwt_token(self, expiration_hours: int) -> str:
        secret_key = self.retrieve_secret_key()
        expiration = int(
            (datetime.now() + timedelta(hours=expiration_hours)).timestamp()
        )
        payload = {
            "iat": int(datetime.now().timestamp()),
            "isLoggedIn": True,
            "exp": expiration,
        }
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        return token
    
    
    def generate_jwt_email_token(self, email, expiration_hours: int) -> str:
        secret_key = self.retrieve_secret_key()
        expiration = int(
            (datetime.now() + timedelta(hours=expiration_hours)).timestamp()
        )
        payload = {
            "iat": int(datetime.now().timestamp()),
            "isLoggedIn": True,
            "exp": expiration,
            "email": email
        }
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        return token

    def rotate_secret_key(self):
        current_date = datetime.now()
        expiration_date = current_date + timedelta(days=30)

        # Load the expiration date from the file if it exists
        if os.path.exists(self.expiration_file_path):
            with open(self.expiration_file_path, "r") as file:
                expiration_date_str = file.read()
                expiration_date = datetime.strptime(expiration_date_str, "%Y-%m-%d")

        # Regenerate the secret key if the expiration date has passed
        if datetime.now() > expiration_date:
            new_secret_key = self.generate_secret_key()
            self.store_secret_key(new_secret_key)
            expiration_date = current_date + timedelta(days=self.expiration_time_day)

        # Save the expiration date to the file
        with open(self.expiration_file_path, "w") as file:
            file.write(expiration_date.strftime("%Y-%m-%d"))


def generate_token(email) -> str:
    token_generator = TokenGenerator(SecretKeyStorage(), "expiration_date.txt")
    token_generator.rotate_secret_key()
    token = token_generator.generate_jwt_email_token(email,expiration_hours=1)
    return token


def check_token_valid(sent_token: str) -> bool:
    token_generator = TokenGenerator(SecretKeyStorage(), "expiration_date.txt")
    key = token_generator.retrieve_secret_key()
    try:
        decoded = jwt.decode(sent_token, key, algorithms=["HS256"])
        return True
    except jwt.ExpiredSignatureError as e:
        print("Signature expired. Please log in again.", str(e))
        return False
    except jwt.InvalidTokenError as e:
        print("Exception message:", str(e))
        return False

def decode_email_from_token(token: str) -> str:
    """
    Decodes the token and returns the email address contained in the token

    Parameters
    ----------
    token : str
        The token to decode

    Returns
    -------
    str
        The email address contained in the token
    """
    token_generator = TokenGenerator(SecretKeyStorage(), "expiration_date.txt")
    key = token_generator.retrieve_secret_key()
    decoded = jwt.decode(token, key, algorithms=["HS256"])
    return decoded["email"]


def do_login(connection: ConnectionParamsHandler, email: str, password: str) -> bool:
    """
    Logs a user in and returns a JSON Web Token to be used in other API calls and the logged in user.

    Args:
        connection (ConnectionParamsHandler): The connection parameters to use to connect to the database.
        email (str): The user's email.
        password (str): The user's password.

    Returns:
        tuple: A tuple containing a JSON serializable dictionary of the logged in user and a JSON Web Token to be used in other API calls or None if the credentials are invalid.
    """
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )
    login_manager = LoginDBAccess(manager=db_manager)
    login_mapper = LoginInfoMapper(
        df=login_manager.get_connection_info_by_email_password(
            email, password
        )
    )
    try:
        logininfomaps_objects = login_mapper.generate_login_infos()
        login_info = logininfomaps_objects[0]
    except IndexError:
        return None, None
    connection_params = login_info.update_connection_params_handler(connection)
    del db_manager
    del login_manager
    del login_mapper
    db_manager = DatabaseManager(
        username=connection_params.username,
        password=connection_params.password,
        ip_address=connection_params.ip_address,
        port=connection_params.port,
        db_name=connection_params.db_name,
    )
    user_manager = UserDBAccess(manager=db_manager)
    user_mapper = UserMapper(
        df_chunk_generator=user_manager.get_user_by_codcf(login_info.codcf)
    )

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
    """
    Retrieves connection parameters from the request.

    This function takes a FastAPI Request object and a ConnectionParamsHandler
    object as parameters. It checks if the provided token is valid, then it
    extracts the email from the request headers and uses it to retrieve the
    connection parameters from the database. The retrieved connection parameters
    are then used to update the ConnectionParamsHandler object and this object is
    returned by the function.

    Args:
        request (Request): The FastAPI Request object containing the headers
            with the token and the email.
        connection (ConnectionParamsHandler): The ConnectionParamsHandler object
            that will be updated with the retrieved connection parameters.

    Returns:
        ConnectionParamsHandler: A ConnectionParamsHandler object with the
            retrieved connection parameters.

    Raises:
        Exception: If the token is invalid or if the credentials are invalid.
    """
    sent_token = request.headers.get("Authorization")
    if not check_token_valid(sent_token=sent_token):
        raise Exception("Invalid credentials")

    email = decode_email_from_token(sent_token) 
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )
    login_manager = LoginDBAccess(manager=db_manager)
    login_mapper = LoginInfoMapper(
        df=login_manager.get_connection_info_by_email(email=email)
    )
    try:
        login_info = login_mapper.generate_login_infos()[0]
    except IndexError:
        raise Exception("Invalid credentials")
    return login_info.update_connection_params_handler(connection)
