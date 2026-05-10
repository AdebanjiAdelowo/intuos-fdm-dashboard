from db_handlers.ibm_db2.db_query_manager import DatabaseManager


class PilotInfoDBAccess:
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

    def get_all_pilot_info(self):
        """
        Retrieves all airplane info from the database.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = "SELECT * FROM ANA.ANACLI"
        return self.__manager.get_query_result(query)
    
    def search_pilots_by_name(self, search_term: str):
        """
        Searches for pilots whose name contains the given search term.
        
        Parameters
        ----------
        search_term : str
            The search term to look for in pilot names.
            
        Returns
        -------
        pandas.DataFrame
            A DataFrame containing pilots whose names match the search term.
        """
        # Using LIKE operator for case-insensitive substring search
        # The exact syntax might vary by database
        query = f"SELECT * FROM ANA.ANACLI WHERE UPPER(ragsoc1) LIKE UPPER('%{search_term}%')"
        return self.__manager.get_query_result(query)
    
    def count_pilots_by_name_search(self, search_term: str, start_date: str, end_date: str):
        """
        Counts pilots whose name contains the given search term.
        
        Parameters
        ----------
        search_term : str
            The search term to look for in pilot names.
            
        Returns
        -------
        int
            The count of matching pilots.                     
                    
        """
        query = f"""
                    SELECT COUNT(*) AS total FROM ANA.ANACLI AN 
                    JOIN (SELECT DISTINCT CODCF_PAGANTE FROM CLUB.CVOLATO CV 
                            WHERE (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) >= '{start_date}' AND (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) <=  '{end_date}'
                            ) FL 
                    ON AN.CODCF = FL.CODCF_PAGANTE  WHERE UPPER(AN.ragsoc1) LIKE UPPER('%{search_term}%')
                """
        result = self.__manager.get_query_result(query)
        return result.iloc[0]['total']
    
    def search_pilots_by_name_pagesize_offset(self, start_date: str, end_date: str, search_term: str, page_size: int, offset:int):        
        
        query = f"""
            SELECT * FROM ANA.ANACLI AN
            JOIN (SELECT DISTINCT CODCF_PAGANTE FROM CLUB.CVOLATO CV 
                            WHERE (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) >= '{start_date}' AND (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) <=  '{end_date}'
                            ) FL 
                    ON AN.CODCF = FL.CODCF_PAGANTE 
            WHERE UPPER(ragsoc1) LIKE UPPER('%{search_term}%')
            ORDER BY ragsoc1
            LIMIT {page_size} OFFSET {offset}
        """
        result = self.__manager.get_query_result(query)
        return result
    
    def pilots_by_name_pagesize_offset(self, start_date: str, end_date: str, page_size: int, offset:int):        
        
        query = f"""
            SELECT * FROM ANA.ANACLI AN
            JOIN (SELECT DISTINCT CODCF_PAGANTE FROM CLUB.CVOLATO CV 
                            WHERE (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) >= '{start_date}' AND (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) <=  '{end_date}'
                            ) FL 
                    ON AN.CODCF = FL.CODCF_PAGANTE 
            ORDER BY ragsoc1
            LIMIT {page_size} OFFSET {offset}
        """
        result = self.__manager.get_query_result(query)
        return result
    
    def get_paginated_pilot_info(self, start_date: str, end_date: str, offset: int, limit: int):
        """
        Retrieves paginated pilot info from the database.
        
        Parameters
        ----------
        offset : int
            The number of records to skip.
        limit : int
            The maximum number of records to return.
            
        Returns
        -------
        pandas.DataFrame
            A DataFrame containing the paginated results of the query.
        """
        # For most SQL databases:
        query = f"""
                    SELECT * FROM ANA.ANACLI AN 
                    JOIN (SELECT DISTINCT CODCF_PAGANTE FROM CLUB.CVOLATO CV 
                            WHERE (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) >= '{start_date}' AND (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) <=  '{end_date}'
                            ) FL 
                    ON AN.CODCF = FL.CODCF_PAGANTE 
                    ORDER BY codcf OFFSET {offset} ROWS FETCH NEXT {limit} ROWS ONLY
                """
    
        # For databases that don't support the above syntax (like MySQL):
        # query = f"SELECT * FROM ANA.ANACLI ORDER BY codcf LIMIT {limit} OFFSET {offset}"
        
        return self.__manager.get_query_result(query)
    
    def get_total_pilot_count(self, start_date, end_date):
        """
        Returns the total number of pilots in the database.
        
        Returns
        -------
        int
            The total number of pilots.
        """
        # query = "SELECT COUNT(*) AS total FROM ANA.ANACLI"
        query = f"""
                    SELECT COUNT(DISTINCT CODCF_PAGANTE) AS total FROM CLUB.CVOLATO CV 
                    WHERE (CV.DATA_VOLO || ' ' || CV.STICK_TAKEOFF) >= '{start_date}' AND (CV.DATA_VOLO || ' ' || CV.STICK_LANDING) <=  '{end_date}'
                """
        result = self.__manager.get_query_result(query)
        return result.iloc[0]['total']
    
    def get_all_pilot_with_flights_info(self):
        """
        Retrieves all airplane info from the database.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = "SELECT * FROM ANA.ANACLI WHERE CODCF IN (SELECT DISTINCT CODCF_PAGANTE FROM CLUB.CVOLATO CV)"
        return self.__manager.get_query_result(query)
    
    
    def get_all_pilot_count(self):
        """
        Retrieves all pilot info from the database.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = "SELECT COUNT(*) AS pilots_count FROM ANA.ANACLI"
        return self.__manager.get_query_result(query)
    
    def get_all_pilot_with_flights_count(self):
        """
        Retrieves all pilot info from the database.

        Returns
        -------
        generator
            A generator which yields a pandas DataFrame containing the results of the query, chunk by chunk.
        """
        query = "SELECT COUNT(DISTINCT CODCF_PAGANTE) AS pilots_count FROM CLUB.CVOLATO CV"
        return self.__manager.get_query_result(query)

