import yaml


class ConnectionParamsHandler:
    def __init__(self, connection_filename: str = None):
        """
        Constructor for ConnectionParamsHandler.

        If connection_filename is None, initializes __config as a dictionary
        with a key "database" mapping to an empty dictionary. Otherwise, reads
        the file at connection_filename and sets __config to its contents.

        Parameters
        ----------
        connection_filename : str
            Path to a YAML file containing connection parameters.

        Returns
        -------
        None
        """
        self.__config = None
        if connection_filename is None:
            self.__config = {"database": {}}
            return
        with open(connection_filename, "r") as file:
            self.__config = yaml.safe_load(file)

    @property
    def username(self) -> str:
        """
        Getter for the username connection parameter.

        Returns
        -------
        str
            Username to use when connecting to the database.
        """
        return self.__config["database"]["username"]

    @property
    def password(self) -> str:
        """
        Getter for the password connection parameter.

        Returns
        -------
        str
            Password to use when connecting to the database.
        """
        return self.__config["database"]["password"]

    @property
    def ip_address(self) -> str:
        """
        Getter for the ip_address connection parameter.

        Returns
        -------
        str
            IP address or hostname of the database server.
        """
        return self.__config["database"]["ip_address"]

    @property
    def port(self) -> str:
        """
        Getter for the port connection parameter.

        Returns
        -------
        str
            TCP port number to use when connecting to the database.
        """
        return self.__config["database"]["port"]

    @property
    def db_name(self) -> str:
        """
        Getter for the db_name connection parameter.

        Returns
        -------
        str
            Name of the database to connect to.
        """
        return self.__config["database"]["db_name"]

    @username.setter
    def username(self, value: str):
        """
        Setter for the username connection parameter.

        Parameters
        ----------
        value : str
            New value for the username connection parameter.

        Returns
        -------
        None
        """
        self.__config["database"]["username"] = value

    @password.setter
    def password(self, value: str):
        """
        Setter for the password connection parameter.

        Parameters
        ----------
        value : str
            New value for the password connection parameter.

        Returns
        -------
        None
        """
        self.__config["database"]["password"] = value

    @ip_address.setter
    def ip_address(self, value: str):
        """
        Setter for the ip_address connection parameter.

        Parameters
        ----------
        value : str
            New value for the ip_address connection parameter.

        Returns
        -------
        None
        """
        self.__config["database"]["ip_address"] = value

    @port.setter
    def port(self, value: str):
        """
        Setter for the port connection parameter.

        Parameters
        ----------
        value : str
            New value for the port connection parameter.

        Returns
        -------
        None
        """
        self.__config["database"]["port"] = value

    @db_name.setter
    def db_name(self, value: str):
        """
        Setter for the db_name connection parameter.

        Parameters
        ----------
        value : str
            New value for the db_name connection parameter.

        Returns
        -------
        None
        """
        self.__config["database"]["db_name"] = value

    def save(self, connection_filename: str):
        """
        Saves the current connection parameters to a file.

        Parameters
        ----------
        connection_filename : str
            Path to a file where the connection parameters will be saved in YAML format.

        Returns
        -------
        None
        """
        with open(connection_filename, "w") as file:
            yaml.dump(self.__config, file)
