from db_handlers.ibm_db2.db_query_manager import DatabaseManager


class PilotDBAccess:
    def __init__(self, manager: DatabaseManager) -> None:
        """
        Initialize the FlightDBAccess object.

        Parameters
        ----------
        manager : DatabaseManager
            A DatabaseManager object to handle database operations.

        Returns
        -------
        None
        """
        self.__manager = manager

    def get_all_pilots(self):
        """
        Retrieves all flights from the database.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = "SELECT * FROM ANA.ANACLI"
        # return self.__manager.get_query_result_generator(query)
        return self.__manager.get_query_result(query)
