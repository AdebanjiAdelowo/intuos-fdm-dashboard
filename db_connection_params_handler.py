import os
from pathlib import Path
from typing import Optional

import yaml


class ConnectionParamsHandler:
    REQUIRED_DATABASE_KEYS = ("username", "password", "ip_address", "port", "db_name")

    def __init__(
        self,
        connection_filename: Optional[str] = None,
        config: Optional[dict] = None,
        section: str = "database",
    ):
        """
        Manage DB2 connection parameters.

        Parameters can be provided directly, loaded from YAML, or loaded from the
        environment via ``from_environment``. The YAML shape is kept backwards
        compatible with the original project::

            database:
              username: ...
              password: ...
              ip_address: ...
              port: ...
              db_name: ...
        """
        self._section = section
        if config is not None:
            raw = config
        elif connection_filename is None:
            raw = {"database": {}}
        else:
            path = Path(connection_filename)
            if not path.exists():
                raise FileNotFoundError(
                    f"Database config file not found: {connection_filename}. "
                    "Create config.yml from config.example.yml or set DATABASE_* env vars."
                )
            with path.open("r") as file:
                raw = yaml.safe_load(file) or {"database": {}}

        # Normalise: expose the requested section under the "database" key so the
        # rest of the class (which always reads self.__config["database"]) works
        # unchanged regardless of which section was requested.
        if section != "database" and section in raw:
            self.__config = {"database": raw[section]}
        else:
            self.__config = raw

        self.__config.setdefault("database", {})
        self._validate_database_config()

    @classmethod
    def from_environment(cls) -> "ConnectionParamsHandler":
        """Build connection parameters from DATABASE_* environment variables."""
        database = {
            "username": os.getenv("DATABASE_USERNAME"),
            "password": os.getenv("DATABASE_PASSWORD"),
            "ip_address": os.getenv("DATABASE_HOST") or os.getenv("DATABASE_IP_ADDRESS"),
            "port": os.getenv("DATABASE_PORT"),
            "db_name": os.getenv("DATABASE_NAME") or os.getenv("DATABASE_DB_NAME"),
        }
        return cls(config={"database": database})

    @classmethod
    def from_environment_or_file(cls, connection_filename: str = "config.yml") -> "ConnectionParamsHandler":
        """
        Prefer DATABASE_* environment variables, falling back to a local YAML file.

        ``ANALYSIS_DASHBOARD_CONFIG`` can point to a non-default YAML path.
        """
        env_keys = (
            "DATABASE_USERNAME",
            "DATABASE_PASSWORD",
            "DATABASE_HOST",
            "DATABASE_IP_ADDRESS",
            "DATABASE_PORT",
            "DATABASE_NAME",
            "DATABASE_DB_NAME",
        )
        if any(os.getenv(key) for key in env_keys):
            return cls.from_environment()
        return cls(connection_filename=os.getenv("ANALYSIS_DASHBOARD_CONFIG", connection_filename))

    def _validate_database_config(self) -> None:
        database = self.__config.get("database") or {}
        missing = [key for key in self.REQUIRED_DATABASE_KEYS if not database.get(key)]
        if missing:
            raise ValueError(
                "Missing database config value(s): "
                + ", ".join(missing)
                + ". Set DATABASE_* env vars or update config.yml."
            )

    @property
    def username(self) -> str:
        return self.__config["database"]["username"]

    @property
    def password(self) -> str:
        return self.__config["database"]["password"]

    @property
    def ip_address(self) -> str:
        return self.__config["database"]["ip_address"]

    @property
    def port(self) -> str:
        return str(self.__config["database"]["port"])

    @property
    def db_name(self) -> str:
        return self.__config["database"]["db_name"]

    @username.setter
    def username(self, value: str):
        self.__config["database"]["username"] = value

    @password.setter
    def password(self, value: str):
        self.__config["database"]["password"] = value

    @ip_address.setter
    def ip_address(self, value: str):
        self.__config["database"]["ip_address"] = value

    @port.setter
    def port(self, value: str):
        self.__config["database"]["port"] = str(value)

    @db_name.setter
    def db_name(self, value: str):
        self.__config["database"]["db_name"] = value

    def save(self, connection_filename: str):
        """Save the current connection parameters to a YAML file."""
        with open(connection_filename, "w") as file:
            yaml.safe_dump(self.__config, file)
