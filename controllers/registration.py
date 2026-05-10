from db_connection_params_handler import ConnectionParamsHandler
from db_handlers.ibm_db2.airplane_info_db_access import AirplaneInfoDBAccess
from db_handlers.ibm_db2.db_query_manager import DatabaseManager
from mappers.airplaneinfo_mapper import AirplaneInfoMapper


def get_all_registrations_count(connection: ConnectionParamsHandler) -> list:
    """
    Retrieves all registrations from the database.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a registration, containing the registration information.
    """
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )
    registration_getter = AirplaneInfoDBAccess(manager=db_manager)
    
    df_chunk_generator= registration_getter.get_all_airplane_count()

    return df_chunk_generator["aircrafts_count"][0]

def get_all_registrations_with_flights_count(connection: ConnectionParamsHandler) -> list:
    """
    Retrieves all registrations from the database.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a registration, containing the registration information.
    """
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )
    registration_getter = AirplaneInfoDBAccess(manager=db_manager)
    
    df_chunk_generator= registration_getter.get_all_airplane_with_flights_count()

    return df_chunk_generator["aircrafts_count"][0]


def get_all_registrations(connection: ConnectionParamsHandler) -> list:
    """
    Retrieves all registrations from the database.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a registration, containing the registration information.
    """
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )
    registration_getter = AirplaneInfoDBAccess(manager=db_manager)
    df_chunk_generator=registration_getter.get_all_airplane_info()
    if df_chunk_generator.dropna(how='all').empty:
        return []
    registration_mapper = AirplaneInfoMapper(df_chunk_generator=df_chunk_generator)
    return [
        airplane_datasheet.as_dict()
        for airplane_datasheet in registration_mapper.generate_airplane_datasheets()
    ]


def get_all_registrations_with_flights(connection: ConnectionParamsHandler) -> list:
    """
    Retrieves all registrations from the database.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a registration, containing the registration information.
    """
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )
    registration_getter = AirplaneInfoDBAccess(manager=db_manager)
    df_chunk_generator=registration_getter.get_all_airplane_with_flights_info()
    if df_chunk_generator.dropna(how='all').empty:
        return []
    registration_mapper = AirplaneInfoMapper(df_chunk_generator=df_chunk_generator)
    return [
        airplane_datasheet.as_dict()
        for airplane_datasheet in registration_mapper.generate_airplane_datasheets()
    ]