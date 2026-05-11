from db_handlers.ibm_db2.db_query_manager import DatabaseManager


class FlightDBAccess:
    def __init__(self, manager: DatabaseManager) -> None:
        self.__manager = manager

    def get_all_flights(self):
        query = "SELECT * FROM ETL.VOLI"
        return self.__manager.get_query_result(query)

    def get_flights_by_datetime_interval(self, start_datetime: str, end_datetime: str):
        query = """
            SELECT *
            FROM ETL.VOLI
            WHERE DATA_ORA_DECOLLO >= ?
              AND DATA_ORA_ATTERRAGGIO <= ?
        """
        return self.__manager.get_query_result(query, (start_datetime, end_datetime))

    def get_flights_by_marche(self, marca: str):
        query = "SELECT * FROM ETL.VOLI WHERE MARCHE = ?"
        return self.__manager.get_query_result(query, (marca,))

    def get_flights_by_marche_datetime_interval(
        self, marca: str, start_date: str, end_date: str
    ):
        query = """
            SELECT *
            FROM ETL.VOLI
            WHERE MARCHE = ?
              AND DATA_ORA_DECOLLO >= ?
              AND DATA_ORA_ATTERRAGGIO <= ?
        """
        return self.__manager.get_query_result(query, (marca, start_date, end_date))

    def get_flewhourmin_by_marche_datetime_interval(
        self, marca: str, start_date: str, end_date: str
    ):
        query = """
            WITH time_duration AS (
                SELECT
                    SUM(TIMESTAMPDIFF(2, CHAR(DATA_ORA_ATTERRAGGIO - DATA_ORA_DECOLLO))) AS duration
                FROM ETL.VOLI
                WHERE MARCHE = ?
                  AND DATA_ORA_DECOLLO >= ?
                  AND DATA_ORA_ATTERRAGGIO <= ?
            )
            SELECT
                FLOOR(duration / 3600) AS hours,
                FLOOR((duration % 3600) / 60) AS minutes,
                MOD(duration, 60) AS seconds
            FROM time_duration
        """
        return self.__manager.get_query_result(query, (marca, start_date, end_date))

    def get_flights_by_marches_datetime_interval(
        self, marcas: list, start_date: str, end_date: str
    ):
        if not marcas:
            return self.__manager.get_query_result("SELECT * FROM ETL.VOLI WHERE 1 = 0")
        placeholders = ", ".join("?" for _ in marcas)
        query = f"""
            SELECT *
            FROM ETL.VOLI
            WHERE MARCHE IN ({placeholders})
              AND DATA_ORA_DECOLLO >= ?
              AND DATA_ORA_ATTERRAGGIO <= ?
        """
        return self.__manager.get_query_result(query, tuple(marcas) + (start_date, end_date))

    def get_flight_by_id(self, id_volo: int):
        query = "SELECT * FROM ETL.VOLI WHERE ID_VOLO = ?"
        return self.__manager.get_query_result(query, (id_volo,))

    def get_flight_time_duration(self, id_volo: int):
        query = """
            SELECT
                FLOOR(TIMESTAMPDIFF(2, CHAR(DATA_ORA_ATTERRAGGIO - DATA_ORA_DECOLLO)) / 3600) AS hours,
                FLOOR((TIMESTAMPDIFF(2, CHAR(DATA_ORA_ATTERRAGGIO - DATA_ORA_DECOLLO)) % 3600) / 60) AS minutes,
                MOD(TIMESTAMPDIFF(2, CHAR(DATA_ORA_ATTERRAGGIO - DATA_ORA_DECOLLO)), 60) AS seconds
            FROM ETL.VOLI
            WHERE ID_VOLO = ?
        """
        return self.__manager.get_query_result(query, (id_volo,))
