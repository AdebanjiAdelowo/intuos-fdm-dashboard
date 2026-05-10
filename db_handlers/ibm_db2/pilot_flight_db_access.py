from db_handlers.ibm_db2.db_query_manager import DatabaseManager


class PilotFlightDBAccess:
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

    def get_all_pilots_flights(self):
        """
        Retrieves all flights from the database.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = """
                SELECT 
                    CV.CODCF_PAGANTE AS id_volo,
                    CV.MARCHE AS marche,
                    (CV.DATA_VOLO || ' ' || CV.BLOCK_TAKEOFF) AS data_ora_decollo,
                    (CV.DATA_VOLO || ' ' || CV.BLOCK_LANDING) AS data_ora_atterraggio,
                    (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) AS apt_takeoff,
                    (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) AS apt_landing
                FROM CLUB.CVOLATO CV
                """
        # return self.__manager.get_query_result_generator(query)
        return self.__manager.get_query_result(query)

    def get_pilots_flights_by_datetime_interval(self, start_datetime: str, end_datetime: str):
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
        query = f"""
                SELECT 
                    CV.CODCF_PAGANTE AS id_volo,
                    CV.MARCHE AS marche,
                    (CV.DATA_VOLO || ' ' || CV.BLOCK_TAKEOFF) AS data_ora_decollo,
                    (CV.DATA_VOLO || ' ' || CV.BLOCK_LANDING) AS data_ora_atterraggio,
                    (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) AS apt_takeoff,
                    (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) AS apt_landing
                FROM CLUB.CVOLATO CV WHERE (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) >= '{start_datetime}' 
                        AND (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) <=  '{end_datetime}'
        """
        return self.__manager.get_query_result(query)

    def get_flights_by_pilot(self, pilot_id: str):
        """
        Retrieves flights from the database based on the given marche.

        Parameters
        ----------
        pilot_id : str
            The pilot to filter by.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = f"""               
                  SELECT 
                    CV.CODCF_PAGANTE AS id_volo,
                    CV.MARCHE AS marche,
                    (CV.DATA_VOLO || ' ' || CV.BLOCK_TAKEOFF) AS data_ora_decollo,
                    (CV.DATA_VOLO || ' ' || CV.BLOCK_LANDING) AS data_ora_atterraggio,
                    (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) AS apt_takeoff,
                    (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) AS apt_landing
                FROM CLUB.CVOLATO CV WHERE CV.CODCF_PAGANTE = '{pilot_id}'
                """
        return self.__manager.get_query_result(query)

    def get_flights_by_pilot_datetime_interval(
        self, pilot_id: str, start_date: str, end_date: str
    ):
        """
        Retrieves flights from the database based on the given marche and datetime interval.

        Parameters
        ----------
        pilot_id : str
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
                SELECT 
                    CV.CODCF_PAGANTE AS id_volo,
                    CV.MARCHE AS marche,
                    (CV.DATA_VOLO || ' ' || CV.BLOCK_TAKEOFF) AS data_ora_decollo,
                    (CV.DATA_VOLO || ' ' || CV.BLOCK_LANDING) AS data_ora_atterraggio,
                    (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) AS apt_takeoff,
                    (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) AS apt_landing
                FROM CLUB.CVOLATO CV
                WHERE CV.CODCF_PAGANTE = '{pilot_id}' AND (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) >= '{start_date}' 
                    AND (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) <=  '{end_date}'
                """
        return self.__manager.get_query_result(query)
    
    def get_flewhourmin_by_pilot_datetime_interval(
        self, pilot_id: str, start_date: str, end_date: str
    ):
        """
        Retrieves flights from the database based on the given marche and datetime interval.

        Parameters
        ----------
        pilot_id : str
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
                    SUM(TIMESTAMPDIFF(2, CHAR(STICK_LANDING - STICK_TAKEOFF))) AS duration
                FROM CLUB.CVOLATO CV 
                    WHERE CV.CODCF_PAGANTE = '{pilot_id}' AND (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) >= '{start_date}' 
                AND (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) <=  '{end_date}'
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
    
    def get_flights_by_pilots_datetime_interval(
        self, pilots: list[str], start_date: str, end_date: str
    ):
        """
        Retrieves flights from the database based on the given marche and datetime interval.

        Parameters
        ----------
        pilots : str
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
                SELECT 
                    CV.CODCF_PAGANTE AS id_volo,
                    CV.MARCHE AS marche,
                    (CV.DATA_VOLO || ' ' || CV.BLOCK_TAKEOFF) AS data_ora_decollo,
                    (CV.DATA_VOLO || ' ' || CV.BLOCK_LANDING) AS data_ora_atterraggio,
                    (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) AS apt_takeoff,
                    (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) AS apt_landing
                FROM CLUB.CVOLATO CV
                WHERE CV.CODCF_PAGANTE IN {tuple(pilots)} 
                        AND (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) >= '{start_date}' 
                        AND (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) <=  '{end_date}'
                """
        return self.__manager.get_query_result(query)

    def get_pilot_flight_by_id(self, pilot_id: int):
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
                    CV.CODCF_PAGANTE AS id_volo,
                    CV.MARCHE AS marche,
                    (CV.DATA_VOLO || ' ' || CV.BLOCK_TAKEOFF) AS data_ora_decollo,
                    (CV.DATA_VOLO || ' ' || CV.BLOCK_LANDING) AS data_ora_atterraggio,
                    (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) AS apt_takeoff,
                    (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) AS apt_landing
                FROM CLUB.CVOLATO CV WHERE CV.CODCF_PAGANTE = '{pilot_id}'
                """
        return self.__manager.get_query_result(query)
    
    def get_pilot_flight_time_duration(self, pilot_id: int):
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
                    FLOOR(TIMESTAMPDIFF(2, CHAR(STICK_LANDING - STICK_TAKEOFF)) / 3600) AS hours,
                    FLOOR((TIMESTAMPDIFF(2, CHAR(STICK_LANDING - STICK_TAKEOFF)) % 3600) / 60) AS minutes,
                    MOD(TIMESTAMPDIFF(2, CHAR(STICK_LANDING - STICK_TAKEOFF)), 60) AS seconds
			FROM CLUB.CVOLATO CV WHERE CV.CODCF_PAGANTE = '{pilot_id}'
        """
        return self.__manager.get_query_result(query)
