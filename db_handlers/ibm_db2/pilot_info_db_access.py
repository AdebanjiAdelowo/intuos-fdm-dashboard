from db_handlers.ibm_db2.db_query_manager import DatabaseManager


class PilotInfoDBAccess:
    def __init__(self, manager: DatabaseManager) -> None:
        self.__manager = manager

    def get_all_pilot_info(self):
        query = "SELECT * FROM ANA.ANACLI"
        return self.__manager.get_query_result(query)

    def search_pilots_by_name(self, search_term: str):
        query = "SELECT * FROM ANA.ANACLI WHERE UPPER(ragsoc1) LIKE UPPER(?)"
        return self.__manager.get_query_result(query, (f"%{search_term}%",))

    def count_pilots_by_name_search(self, search_term: str, start_date: str, end_date: str):
        query = """
            SELECT COUNT(*) AS total
            FROM ANA.ANACLI AN
            JOIN (
                SELECT DISTINCT CODCF_PAGANTE
                FROM CLUB.CVOLATO CV
                WHERE (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) >= ?
                  AND (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) <= ?
            ) FL ON AN.CODCF = FL.CODCF_PAGANTE
            WHERE UPPER(AN.ragsoc1) LIKE UPPER(?)
        """
        result = self.__manager.get_query_result(query, (start_date, end_date, f"%{search_term}%"))
        return result.iloc[0]["total"]

    def search_pilots_by_name_pagesize_offset(
        self, start_date: str, end_date: str, search_term: str, page_size: int, offset: int
    ):
        query = """
            SELECT *
            FROM ANA.ANACLI AN
            JOIN (
                SELECT DISTINCT CODCF_PAGANTE
                FROM CLUB.CVOLATO CV
                WHERE (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) >= ?
                  AND (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) <= ?
            ) FL ON AN.CODCF = FL.CODCF_PAGANTE
            WHERE UPPER(ragsoc1) LIKE UPPER(?)
            ORDER BY ragsoc1
            LIMIT ? OFFSET ?
        """
        return self.__manager.get_query_result(
            query, (start_date, end_date, f"%{search_term}%", int(page_size), int(offset))
        )

    def pilots_by_name_pagesize_offset(
        self, start_date: str, end_date: str, page_size: int, offset: int
    ):
        query = """
            SELECT *
            FROM ANA.ANACLI AN
            JOIN (
                SELECT DISTINCT CODCF_PAGANTE
                FROM CLUB.CVOLATO CV
                WHERE (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) >= ?
                  AND (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) <= ?
            ) FL ON AN.CODCF = FL.CODCF_PAGANTE
            ORDER BY ragsoc1
            LIMIT ? OFFSET ?
        """
        return self.__manager.get_query_result(query, (start_date, end_date, int(page_size), int(offset)))

    def get_paginated_pilot_info(self, start_date: str, end_date: str, offset: int, limit: int):
        query = """
            SELECT *
            FROM ANA.ANACLI AN
            JOIN (
                SELECT DISTINCT CODCF_PAGANTE
                FROM CLUB.CVOLATO CV
                WHERE (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) >= ?
                  AND (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) <= ?
            ) FL ON AN.CODCF = FL.CODCF_PAGANTE
            ORDER BY codcf OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """
        return self.__manager.get_query_result(query, (start_date, end_date, int(offset), int(limit)))

    def get_total_pilot_count(self, start_date, end_date):
        query = """
            SELECT COUNT(DISTINCT CODCF_PAGANTE) AS total
            FROM CLUB.CVOLATO CV
            WHERE (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) >= ?
              AND (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) <= ?
        """
        result = self.__manager.get_query_result(query, (start_date, end_date))
        return result.iloc[0]["total"]

    def get_all_pilot_with_flights_info(self):
        query = """
            SELECT *
            FROM ANA.ANACLI
            WHERE CODCF IN (SELECT DISTINCT CODCF_PAGANTE FROM CLUB.CVOLATO CV)
        """
        return self.__manager.get_query_result(query)

    def get_all_pilot_count(self):
        query = "SELECT COUNT(*) AS pilots_count FROM ANA.ANACLI"
        return self.__manager.get_query_result(query)

    def get_all_pilot_with_flights_count(self):
        query = "SELECT COUNT(DISTINCT CODCF_PAGANTE) AS pilots_count FROM CLUB.CVOLATO CV"
        return self.__manager.get_query_result(query)
