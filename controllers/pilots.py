from db_connection_params_handler import ConnectionParamsHandler
from db_handlers.ibm_db2.pilot_info_db_access import PilotInfoDBAccess
from db_handlers.ibm_db2.db_query_manager import DatabaseManager
from db_factory import make_db_manager
from mappers.pilotinfo_mapper import PilotInfoMapper


def get_all_pilots_count(connection: ConnectionParamsHandler) -> list:
    """
    Retrieves all pilots from the database.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a registration, containing the registration information.
    """
    db_manager = make_db_manager(connection)
    pilot_getter = PilotInfoDBAccess(manager=db_manager)
    
    df_chunk_generator= pilot_getter.get_all_pilot_count()

    return df_chunk_generator["pilots_count"][0] 

def get_all_pilots_with_flights_count(connection: ConnectionParamsHandler) -> list:
    """
    Retrieves all pilots from the database.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a pilot, containing the pilot information.
    """
    db_manager = make_db_manager(connection)
    pilot_getter = PilotInfoDBAccess(manager=db_manager)
    
    df_chunk_generator= pilot_getter.get_all_pilot_with_flights_count()

    return df_chunk_generator["pilots_count"][0]


def get_all_pilots(connection: ConnectionParamsHandler) -> list:
    """
    Retrieves all pilots from the database.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a pilot, containing the pilot information.
    """
    db_manager = make_db_manager(connection)
    pilot_getter = PilotInfoDBAccess(manager=db_manager)
    df_chunk_generator=pilot_getter.get_all_pilot_info()
    if df_chunk_generator.dropna().empty:
        return []
    pilot_mapper = PilotInfoMapper(df_chunk_generator=df_chunk_generator)
    return [
        pilot_datasheet.as_dict()
        for pilot_datasheet in pilot_mapper.generate_pilot_datasheets()
    ]

def get_paginated_pilots(connection: ConnectionParamsHandler, start_date:str, end_date: str, page: int, page_size: int) -> tuple:
    """
    Retrieves a paginated list of pilots from the database.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.
    page : int
        The page number (1-based).
    page_size : int
        The number of records per page.

    Returns
    -------
    tuple
        A tuple containing (list of pilot dictionaries, total count of pilots).
    """
    db_manager = make_db_manager(connection)
    
    pilot_getter = PilotInfoDBAccess(manager=db_manager)
    
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Get total count first for pagination metadata
    total_count = pilot_getter.get_total_pilot_count(start_date=start_date, end_date=end_date)
    
    # If no records, return early
    if total_count == 0:
        return [], 0
    
    # Get the paginated data
    df_chunk = pilot_getter.get_paginated_pilot_info(start_date=start_date, end_date=end_date, offset=offset, limit=page_size)
    
    if df_chunk.dropna(how='all').empty:
        return [], total_count
        
    # Map the records to pilot datasheets
    pilot_mapper = PilotInfoMapper(df_chunk_generator=df_chunk)
    pilots = [
        pilot_datasheet.as_dict()
        for pilot_datasheet in pilot_mapper.generate_pilot_datasheets()
    ]
    
    return pilots, total_count


def search_pilots(connection: ConnectionParamsHandler, start_date: str, end_date: str, search_term: str = None, page: int = 1, page_size: int = 10) -> tuple:
    """
    Searches for pilots by name and returns paginated results.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.
    search_term : str, optional
        The search term to filter pilots by name.
    page : int
        The page number (1-based).
    page_size : int
        The number of records per page.

    Returns
    -------
    tuple
        A tuple containing (list of pilot dictionaries, total count of matching pilots).
    """
    db_manager = make_db_manager(connection)
    
    pilot_getter = PilotInfoDBAccess(manager=db_manager)
    
    # Calculate offset for pagination
    offset = (page - 1) * page_size
    
    # If search term is provided, use search method
    if search_term:
        # Get total count first for pagination metadata
        total_count = pilot_getter.count_pilots_by_name_search(search_term, start_date, end_date)
        
        # If no records, return early
        if total_count == 0:
            return [], 0
        
        df_chunk = pilot_getter.search_pilots_by_name_pagesize_offset(start_date, end_date,search_term,page_size,offset)
    else:
        # If no search term, get all pilots (paginated)
        total_count = pilot_getter.get_total_pilot_count(start_date, end_date)
        
        if total_count == 0:
            return [], 0
            
        df_chunk = pilot_getter.pilots_by_name_pagesize_offset(start_date, end_date,page_size,offset)
    
    if df_chunk.dropna(how='all').empty:
        return [], total_count
        
    # Map the records to pilot datasheets
    pilot_mapper = PilotInfoMapper(df_chunk_generator=df_chunk)
    pilots = [
        pilot_datasheet.as_dict()
        for pilot_datasheet in pilot_mapper.generate_pilot_datasheets()
    ]
    
    return pilots, int(total_count)

def get_all_pilots_with_flights(connection: ConnectionParamsHandler) -> list:
    """
    Retrieves all pilots from the database.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a registration, containing the registration information.
    """
    db_manager = make_db_manager(connection)
    pilot_getter = PilotInfoDBAccess(manager=db_manager)
    df_chunk_generator=pilot_getter.get_all_pilot_with_flights_info()
    if df_chunk_generator.dropna().empty:
        return []
    pilot_mapper = PilotInfoMapper(df_chunk_generator=df_chunk_generator)
    return [
        pilot_datasheet.as_dict()
        for pilot_datasheet in pilot_mapper.generate_pilot_datasheets()
    ]