from db_handlers.ibm_db2.db_query_manager import DatabaseManager


class FlightDBAccess:
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

    def get_all_flights(self):
        """
        Retrieves all flights from the database.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = "SELECT * FROM ETL.VOLI"
        # return self.__manager.get_query_result_generator(query)
        return self.__manager.get_query_result(query)

    def get_flights_by_datetime_interval(self, start_datetime: str, end_datetime: str):
        """
        Retrieves flights from the database based on the given datetime interval.

        Parameters
        ----------
        start_datetime : str
            The start of the datetime interval in ISO 8601 format.
        end_datetime : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f"SELECT * FROM ETL.VOLI WHERE DATA_ORA_DECOLLO >= '{start_datetime}' AND DATA_ORA_ATTERRAGGIO <= '{end_datetime}'"
        return self.__manager.get_query_result(query)

    def get_flights_by_marche(self, marca: str):
        """
        Retrieves flights from the database based on the given marche.

        Parameters
        ----------
        marca : str
            The marche to filter by.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f"SELECT * FROM ETL.VOLI WHERE MARCHE = '{marca}'"
        return self.__manager.get_query_result(query)

    def get_flights_by_marche_datetime_interval(
        self, marca: str, start_date: str, end_date: str
    ):
        """
        Retrieves flights from the database based on the given marche and datetime interval.

        Parameters
        ----------
        marca : str
            The marche to filter by.
        start_date : str
            The start of the datetime interval in ISO 8601 format.
        end_date : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f"SELECT * FROM ETL.VOLI WHERE MARCHE = '{marca}' AND DATA_ORA_DECOLLO >= '{start_date}' AND DATA_ORA_ATTERRAGGIO <= '{end_date}'"
        return self.__manager.get_query_result(query)
    
    def get_flewhourmin_by_marche_datetime_interval(
        self, marca: str, start_date: str, end_date: str
    ):
        """
        Retrieves flights from the database based on the given marche and datetime interval.

        Parameters
        ----------
        marca : str
            The marche to filter by.
        start_date : str
            The start of the datetime interval in ISO 8601 format.
        end_date : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f"""
            WITH time_duration AS (
                SELECT 
                    SUM(TIMESTAMPDIFF(2, CHAR(DATA_ORA_ATTERRAGGIO - DATA_ORA_DECOLLO))) AS duration
                FROM     ETL.VOLI WHERE MARCHE = '{marca}' AND DATA_ORA_DECOLLO >= '{start_date}' AND DATA_ORA_ATTERRAGGIO <= '{end_date}'
                )SELECT 
                    FLOOR(duration / 3600) AS hours,
                    FLOOR((duration % 3600) / 60) AS minutes,
                    MOD(duration, 60) AS seconds
                FROM time_duration
        """
        prequery = """
                SELECT 
                        SUM(DEC(TIMESTAMPDIFF(4, CHAR(TIMESTAMP(DATA_ORA_ATTERRAGGIO) - TIMESTAMP(DATA_ORA_DECOLLO))), 10, 2)) AS total_minutes,
                        SUM(DEC(TIMESTAMPDIFF(8, CHAR(TIMESTAMP(DATA_ORA_ATTERRAGGIO) - TIMESTAMP(DATA_ORA_DECOLLO))), 10, 2)) AS total_hours
                FROM ETL.VOLI
        """
        return self.__manager.get_query_result(query)
    
    def get_flights_by_marches_datetime_interval(
        self, marcas: list[str], start_date: str, end_date: str
    ):
        """
        Retrieves flights from the database based on the given marche and datetime interval.

        Parameters
        ----------
        marca : str
            The marche to filter by.
        start_date : str
            The start of the datetime interval in ISO 8601 format.
        end_date : str
            The end of the datetime interval in ISO 8601 format.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f"SELECT * FROM ETL.VOLI WHERE MARCHE IN {tuple(marcas)} AND DATA_ORA_DECOLLO >= '{start_date}' AND DATA_ORA_ATTERRAGGIO <= '{end_date}'"
        return self.__manager.get_query_result(query)

    def get_flight_by_id(self, id_volo: int):
        """
        Retrieves a flight from the database based on the given id_volo.

        Parameters
        ----------
        id_volo : int
            The id of the flight to retrieve.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f"SELECT * FROM ETL.VOLI WHERE ID_VOLO = '{id_volo}'"
        return self.__manager.get_query_result(query)
    
    def get_flight_time_duration(self, id_volo: int):
        """
        Retrieves a flight from the database based on the given id_volo.

        Parameters
        ----------
        id_volo : int
            The id of the flight to retrieve.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f"""
            SELECT 
                    FLOOR(TIMESTAMPDIFF(2, CHAR(DATA_ORA_ATTERRAGGIO - DATA_ORA_DECOLLO)) / 3600) AS hours,
                    FLOOR((TIMESTAMPDIFF(2, CHAR(DATA_ORA_ATTERRAGGIO - DATA_ORA_DECOLLO)) % 3600) / 60) AS minutes,
                    MOD(TIMESTAMPDIFF(2, CHAR(DATA_ORA_ATTERRAGGIO - DATA_ORA_DECOLLO)), 60) AS seconds
			FROM ETL.VOLI WHERE ID_VOLO =  '{id_volo}'
        """
        return self.__manager.get_query_result(query)
