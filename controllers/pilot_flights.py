import datetime
import pandas as pd

from db_connection_params_handler import ConnectionParamsHandler
from db_handlers.ibm_db2.db_query_manager import DatabaseManager
from db_handlers.ibm_db2.pilot_flight_db_access import PilotFlightDBAccess
from mappers.flight_mapper import FlightMapper
from datamodels import Flight


def is_date_in_format(date_string):
    """
    Checks if a given string is in the format of a date.

    Parameters
    ----------
    date_string : str
        The string to check.

    Returns
    -------
    bool
        True if the string is in the format of a date, False otherwise.
    """
    try:
        datetime.datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def get_all_flights(connection: ConnectionParamsHandler) -> list: 
    """
    Retrieves all flights from the database.

    Parameters
    ----------
    connection : ConnectionParamsHandler   
        The database connection parameters.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a flight, containing the flight information.
    """
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,  
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )
    flight_getter = PilotFlightDBAccess(manager=db_manager)
    df_chunk_generator=flight_getter.get_all_pilots_flights() 
    if df_chunk_generator.dropna(how='all').empty:
        return []
    flight_mapper = FlightMapper(df_chunk_generator=df_chunk_generator)
    flights = flight_mapper.generate_converted_flights()
    # return [flight.as_dict() for flight in flight_mapper.generate_converted_flights()]
    return flights.apply(Flight.as_dict).tolist()


def get_all_pilot_flights(
    connection: ConnectionParamsHandler, pilot_id: str
) -> list:
    """
    Retrieves all flights for the given registration id.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.
    pilot_id : str
        The pilot id to filter by.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a flight, containing the flight information.
    """
    pilot_id = pilot_id.strip()
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )
    flight_getter = PilotFlightDBAccess(manager=db_manager)
    df_chunk_generator=flight_getter.get_flights_by_pilot(pilot_id=pilot_id)
    if df_chunk_generator.dropna(how='all').empty:
        return []
    df_chunk_generator.rename(columns={'data_ora_decollo':'stick_on', 'data_ora_atterraggio':'stick_off'}, inplace=True)
    
    def safe_format(x):
        if isinstance(x, (pd.Timestamp, datetime.datetime)):
            return x.strftime("%Y-%m-%d %H:%M:%S.%f")
        return x  # Return as is if it's already a string

    df_chunk_generator[['stick_on', 'stick_off']] = df_chunk_generator[['stick_on', 'stick_off']].applymap(safe_format)
    # df_chunk_generator[['stick_on', 'stick_off']] = pd.to_datetime(df_chunk_generator[['stick_on', 'stick_off']])
    # df_chunk_generator[['stick_on', 'stick_off']] = df_chunk_generator[['stick_on', 'stick_off']].map(lambda x: x.strftime("%Y-%m-%d %H:%M:%S.%f"))
    # flight_mapper = FlightMapper(
    #     df_chunk_generator=flight_getter.get_flights_by_marche(marca=registration_id) 
    # )
    # flights = flight_mapper.generate_converted_flights()
    
    # return [flight.as_dict() for flight in flight_mapper.generate_converted_flights()]
    return df_chunk_generator.to_dict(orient='records')


def get_flights_by_pilot_id_and_date(
    connection: ConnectionParamsHandler,
    pilot_id: str,
    start_date: str,
    end_date: str,
) -> list:
    """
    Retrieves all flights for the given registration id and time range.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.
    pilot_id : str
        The pilot id to filter by.
    start_date : str
        The start of the time range in ISO 8601 format.
    end_date : str
        The end of the time range in ISO 8601 format.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a flight, containing the flight information.
    """
    pilot_id = pilot_id.strip()
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )
    flight_getter = PilotFlightDBAccess(manager=db_manager)
    
    df_chunk_generator=flight_getter.get_flights_by_pilot_datetime_interval(
            pilot_id=pilot_id, start_date=start_date, end_date=end_date
        )
    
    # flight_mapper = FlightMapper(
    #     df_chunk_generator=flight_getter.get_flights_by_marche_datetime_interval(
    #         marca=registration_id, start_date=start_date, end_date=end_date
    #     )
    # )
    # flights = flight_mapper.generate_converted_flights()
    # return [flight.as_dict() for flight in flight_mapper.generate_converted_flights()]
    if df_chunk_generator.dropna(how='all').empty:
        return []
    df_chunk_generator.rename(columns={'data_ora_decollo':'stick_on', 'data_ora_atterraggio':'stick_off'}, inplace=True)
    def safe_format(x):
        if isinstance(x, (pd.Timestamp, datetime.datetime)):
            return x.strftime("%Y-%m-%d %H:%M:%S.%f")
        return x  # Return as is if it's already a string

    df_chunk_generator[['stick_on', 'stick_off']] = df_chunk_generator[['stick_on', 'stick_off']].applymap(safe_format)
    flights_length = df_chunk_generator.shape[0]
    result = dict()
    # result["flights"] = df_chunk_generator.to_dict(orient='records')
    result['flights_length'] = flights_length
    return [result]

def get_total_flewhourmin_by_pilot_id_and_date(
    connection: ConnectionParamsHandler,
    pilot_id: str,
    start_date: str,
    end_date: str,
) -> list:
    """
    Retrieves all flights for the given registration id and time range.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.
    pilot_id : str
        The registration id to filter by.
    start_date : str
        The start of the time range in ISO 8601 format.
    end_date : str
        The end of the time range in ISO 8601 format.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a flight, containing the flight information.
    """
    pilot_id = pilot_id.strip()
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )
    flight_getter = PilotFlightDBAccess(manager=db_manager)
    
    df_chunk_generator=flight_getter.get_flewhourmin_by_pilot_datetime_interval(
            pilot_id=pilot_id, start_date=start_date, end_date=end_date
        )
    if df_chunk_generator.dropna(how='all').empty:
        return []
 
    return df_chunk_generator.to_dict(orient='records')

def get_flights_by_pilot_ids_and_date(
    connection: ConnectionParamsHandler,
    pilot_ids: list[str],
    start_date: str,
    end_date: str,
) -> list:
    """
    Retrieves all flights for the given registration id and time range.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.
    registration_ids : list
        The registration ids to filter by.
    start_date : str
        The start of the time range in ISO 8601 format.
    end_date : str
        The end of the time range in ISO 8601 format.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a flight, containing the flight information.
    """
    # registration_id = registration_id.strip()
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )
    flight_getter = PilotFlightDBAccess(manager=db_manager)
    
    if len(pilot_ids) > 1:
        df_chunk_generator=flight_getter.get_flights_by_pilots_datetime_interval(
                marcas=pilot_ids, start_date=start_date, end_date=end_date
            )
    else:
        df_chunk_generator=flight_getter.get_flights_by_pilot_datetime_interval(
            marca=pilot_ids[0], start_date=start_date, end_date=end_date
        )
    
    # flight_mapper = FlightMapper(df_chunk_generator=df_chunk_generator)
    # flights = flight_mapper.generate_converted_flights()
    # # return [flight.as_dict() for flight in flight_mapper.generate_converted_flights()]
    # return flights.apply(Flight.as_dict).tolist()

    if df_chunk_generator.dropna(how='all').empty:
        return []
    df_chunk_generator.rename(columns={'data_ora_decollo':'stick_on', 'data_ora_atterraggio':'stick_off'}, inplace=True)
    df_chunk_generator[['stick_on', 'stick_off']] = df_chunk_generator[['stick_on', 'stick_off']].map(lambda x: x.strftime("%Y-%m-%d %H:%M:%S.%f"))
    return df_chunk_generator.to_dict(orient='records')

