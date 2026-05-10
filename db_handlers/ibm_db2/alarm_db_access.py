from db_handlers.ibm_db2.db_query_manager import DatabaseManager


class AlarmDBAccess:
    def __init__(self, manager: DatabaseManager) -> None:
        """
        Constructor for AlarmDBAccess.

        Parameters
        ----------
        manager : DatabaseManager
            A DatabaseManager object to handle database operations.

        Returns
        -------
        None
        """
        self.__manager = manager

    def get_all_alarms(self):
        """
        Retrieves all alarms from the database.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = "SELECT * FROM BASE.BOX_ALARM"
        return self.__manager.get_query_result(query)

    def get_alarm_by_marca(self, marca: str):
        """
        Retrieves alarms from the database for the given marca.

        Parameters
        ----------
        marca : str
            The marca to filter by.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f"SELECT * FROM BASE.BOX_ALARM WHERE MARCHE = '{marca}'"
        return self.__manager.get_query_result(query)
