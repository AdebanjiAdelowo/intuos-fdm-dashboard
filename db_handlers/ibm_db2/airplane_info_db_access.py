from db_handlers.ibm_db2.db_query_manager import DatabaseManager


class AirplaneInfoDBAccess:
    def __init__(self, manager: DatabaseManager) -> None:
        """
        Constructor for AirplaneInfoDBAccess.

        Parameters
        ----------
        manager : DatabaseManager
            A DatabaseManager object to handle database operations.

        Returns
        -------
        None
        """

        self.__manager = manager

    def get_all_airplane_info(self):
        """
        Retrieves all airplane info from the database.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = "SELECT * FROM ANA.ANAAERO"
        return self.__manager.get_query_result(query)
    
    def get_all_airplane_with_flights_info(self):
        """
        Retrieves all airplane info from the database.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = "SELECT * FROM ANA.ANAAERO WHERE MARCHE IN (SELECT DISTINCT MARCHE FROM ETL.VOLI)"
        return self.__manager.get_query_result(query)
    
    
    def get_all_airplane_count(self):
        """
        Retrieves all airplane info from the database.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = "SELECT COUNT(*) AS aircrafts_count FROM ANA.ANAAERO"
        return self.__manager.get_query_result(query)
    
    def get_all_airplane_with_flights_count(self):
        """
        Retrieves all airplane info from the database.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = "SELECT COUNT(DISTINCT MARCHE) AS aircrafts_count FROM ETL.VOLI"
        return self.__manager.get_query_result(query)

