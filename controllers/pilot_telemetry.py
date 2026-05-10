# import datetime
import pandas as pd
import numpy as np
from db_connection_params_handler import ConnectionParamsHandler
from db_handlers.ibm_db2.MQTT_db_access import TelemetryMQTTDatabaseAccess, PilotTelemetryMQTTDatabaseAccess
from db_handlers.ibm_db2.airplane_info_db_access import AirplaneInfoDBAccess
from db_handlers.ibm_db2.alarm_db_access import AlarmDBAccess
from db_handlers.ibm_db2.db_query_manager import DatabaseManager
from db_handlers.ibm_db2.pilot_flight_db_access import PilotFlightDBAccess
from logic.alarm_assignment import AlarmHandler
# from logic.flight_quality import FlightQualityCalculator
from logic.position_assignment import PositionAssigner
from mappers.airplaneinfo_mapper import AirplaneInfoMapper
from mappers.alarm_mapper import AlarmMapper
from mappers.flight_mapper import FlightMapper
from mappers.telemetry_mapper import (
    FormattedTelemetryMapper,
)

position_assigner = PositionAssigner(
    model_file_path="logic/position_assignment_data/f1.pkl",
    label_names_file_path="logic/position_assignment_data/f1_class_names.json",
    features_file_path="logic/position_assignment_data/f1_selected_features.json",
)
chunksize = 10000


def get_flight_time_duration(
    connection: ConnectionParamsHandler, id: int
) -> list:
    """
    Retrieves the telemetry of a given flight, including the alarms raised during the flight and the labels assigned to the telemetry points.

    Args:
        connection (ConnectionParamsHandler): The database connection parameters.
        id (int): The id of the flight.

    Returns:
        list: A list containing the telemetry samples, each represented as a dictionary, and the flight quality information, which includes the y and z statistics of the takeoff and landing phases.
    """
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )

    flight_getter = PilotFlightDBAccess(manager=db_manager)
    df_chunk_generator=flight_getter.get_flight_time_duration(id_volo=id)
    if df_chunk_generator.dropna(how='all').empty:
        return []
    df_chunk_generator = df_chunk_generator.dropna(axis=1, how='all')
    return df_chunk_generator.to_dict(orient='records')


def get_flight_telemetry_with_alarms_and_labels(
    connection: ConnectionParamsHandler, id: int
) -> list:
    """
    Retrieves the telemetry of a given flight, including the alarms raised during the flight and the labels assigned to the telemetry points.

    Args:
        connection (ConnectionParamsHandler): The database connection parameters.
        id (int): The id of the flight.

    Returns:
        list: A list containing the telemetry samples, each represented as a dictionary, and the flight quality information, which includes the y and z statistics of the takeoff and landing phases.
    """
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )

    flight_getter = PilotFlightDBAccess(manager=db_manager)
    df_chunk_generator=flight_getter.get_flight_by_id(id_volo=id)
    if df_chunk_generator.dropna(how='all').empty:
        return []
    flight_mapper = FlightMapper(df_chunk_generator=df_chunk_generator)

    try:
        flight = flight_mapper.generate_converted_flights().iloc[0]
    except IndexError:
        return []

    telemetry_getter = PilotTelemetryMQTTDatabaseAccess(manager=db_manager)
    
    df_chunk_generator=telemetry_getter.get_telemetry_alarms_by_flight(id_volo=id)
    if df_chunk_generator.dropna(how='all').empty:
        return []
    telemetry_alarms_mapper = FormattedTelemetryMapper(
         df_chunk_generator=df_chunk_generator,
         position_assigner=position_assigner,
    )
    
    telemetry_alarms_samples = telemetry_alarms_mapper.generate_telemetry_alarms()

    info = {
        "telemetry_alarms": list(map(lambda telemetry: telemetry.as_dict(), telemetry_alarms_samples)), 
        "flight_info": flight.as_dict(),
    }

    return info

def get_flight_telemetry_by_pilots_date_range( 
    connection: ConnectionParamsHandler,
    pilot_ids: list[str],
    start_date: str,
    end_date: str,
) -> list[dict]:
    """
    Retrieves all the telemetry samples for a given registration id in the given time range, assigns alarms to the telemetry points, and returns the telemetry samples as a list of dictionaries.

    Args:
        connection (ConnectionParamsHandler): The database connection parameters.
        registration_id (str): The list of id of the registration(s).
        start_date (str): The start of the time range in ISO 8601 format.
        end_date (str): The end of the time range in ISO 8601 format.

    Returns:
        list[dict]: A list of dictionaries, each representing a telemetry sample, containing the telemetry point information and the alarms raised at that point.
    """
    
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )

    telemetry_getter = PilotTelemetryMQTTDatabaseAccess(manager=db_manager)
    
    if len(pilot_ids) > 1:
        pilot_ids = [pilot_id.strip() for pilot_id in pilot_ids]
        df_chunk_generator=telemetry_getter.get_telemetry_by_pilots_datetime_interval(
                pilots=pilot_ids, start_datetime=start_date, end_datetime=end_date
            )
    else:
        df_chunk_generator=telemetry_getter.get_telemetry_by_pilot_datetime_interval(
            pilot=pilot_ids[0].strip(), start_datetime=start_date, end_datetime=end_date
        )
    
    if df_chunk_generator.dropna(how='all').empty:
        return []
    telemetry_mapper = FormattedTelemetryMapper(
        df_chunk_generator=df_chunk_generator,
        position_assigner=position_assigner
    )

    telemetry_objects = telemetry_mapper.generate_telemetry_alarms(has_alarms=True)
    return list(map(lambda telemetry: telemetry.as_dict(), telemetry_objects))



def get_alarms_by_pilot_id(
    connection: ConnectionParamsHandler, pilot_id: str
):
    """
    Retrieves all alarms from the database for the given pilot_id.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.
    pilot_id : str
        The pilot_id to filter by.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a telemetry sample, containing the telemetry point information and the alarms raised at that point.
    """
    pilot_id = pilot_id.strip()
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )

    # alarm_getter = AlarmDBAccess(manager=db_manager)
    # df_alarm_chunk_generator=alarm_getter.get_alarm_by_marca(marca=registration_id)
    # alarm_mapper = AlarmMapper(df_chunk_generator=df_alarm_chunk_generator)
    telemetry_getter = PilotTelemetryMQTTDatabaseAccess(manager=db_manager)
    
    df_alarms_chunk_generator=telemetry_getter.get_alarms_by_pilot(pilot=pilot_id) 
    
    if df_alarms_chunk_generator.dropna(how='all').empty:
        return []
    # telemetry_mapper = UnformattedTelemetryMapper(df_chunk_generator=telemetry_getter.get_telemetry_by_marca_unformatted(marca=registration_id), position_assigner=position_assigner)

    # telemetry_mapper = FormattedTelemetryMapper(df_chunk_generator=df_chunk_generator,position_assigner=position_assigner)
    # alarm_handler = AlarmHandler(alarms=[alarm for alarm in alarm_mapper.generate_alarms()])
    # telemetry = [
    #     alarm_handler.assign_alarm_to_telemetry(telemetry).as_dict()
    #     for telemetry in telemetry_mapper.generate_telemetry_samples()
    # ]
    df_alarms_chunk_generator = df_alarms_chunk_generator.dropna(axis=1, how='all')
    return  df_alarms_chunk_generator.to_dict(orient='records')


def get_all_recent_alarms_by_pilot_id(
    connection: ConnectionParamsHandler, 
    pilot_id: str,
    start_date: str,
    end_date: str
):
    """
    Retrieves all alarms from the database for the given registration_id.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.
    registration_id : str
        The pilot_id to filter by.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a telemetry sample, containing the telemetry point information and the alarms raised at that point.
    """
    pilot_id = pilot_id.strip()
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )

    # alarm_getter = AlarmDBAccess(manager=db_manager)
    # df_alarm_chunk_generator=alarm_getter.get_alarm_by_marca(marca=registration_id)
    # alarm_mapper = AlarmMapper(df_chunk_generator=df_alarm_chunk_generator)
    telemetry_getter = PilotTelemetryMQTTDatabaseAccess(manager=db_manager)
    
    df_alarms_chunk_generator=telemetry_getter.get_alarms_by_pilot_datetime_interval(pilot=pilot_id,
                                                                                     start_datetime=start_date,
                                                                                     end_datetime=end_date
                                                                                     )

    if df_alarms_chunk_generator.dropna(how='all').empty:
        return []
    df_alarms_chunk_generator["total"] = df_alarms_chunk_generator.drop(["registration"], axis=1).sum(axis=1)
    # telemetry_mapper = UnformattedTelemetryMapper(df_chunk_generator=telemetry_getter.get_telemetry_by_marca_unformatted(marca=registration_id), position_assigner=position_assigner)

    # telemetry_mapper = FormattedTelemetryMapper(df_chunk_generator=df_alarms_chunk_generator,position_assigner=position_assigner)
    # alarm_handler = AlarmHandler(alarms=[alarm for alarm in alarm_mapper.generate_alarms()])
    # telemetry = [
    #     alarm_handler.assign_alarm_to_telemetry(telemetry).as_dict()
    #     for telemetry in telemetry_mapper.generate_telemetry_samples()
    # ]
    df_alarms_chunk_generator = df_alarms_chunk_generator.dropna(axis=1, how='all')
    return df_alarms_chunk_generator.to_dict(orient='records')


def get_all_top_recent_alarms_by_pilot_id(
    connection: ConnectionParamsHandler, 
    pilot_id: str,
    top: str,
    start_date: str,
    end_date: str
):
    """
    Retrieves all alarms from the database for the given registration_id.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.
    registration_id : str
        The registration_id to filter by.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a telemetry sample, containing the telemetry point information and the alarms raised at that point.
    """
    pilot_id = pilot_id.strip()
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )

    # alarm_getter = AlarmDBAccess(manager=db_manager)
    # df_alarm_chunk_generator=alarm_getter.get_alarm_by_marca(marca=registration_id)
    # alarm_mapper = AlarmMapper(df_chunk_generator=df_alarm_chunk_generator)
    telemetry_getter = PilotTelemetryMQTTDatabaseAccess(manager=db_manager)
    
    df_alarms_chunk_generator=telemetry_getter.get_alarms_by_pilot_datetime_interval(pilot=pilot_id,
                                                                                     start_datetime=start_date,
                                                                                     end_datetime=end_date
                                                                                     ) 
    if df_alarms_chunk_generator.dropna(how='all').empty:
        return []
    # telemetry_mapper = UnformattedTelemetryMapper(df_chunk_generator=telemetry_getter.get_telemetry_by_marca_unformatted(marca=registration_id), position_assigner=position_assigner)

    # telemetry_mapper = FormattedTelemetryMapper(df_chunk_generator=df_chunk_generator,position_assigner=position_assigner)
    # alarm_handler = AlarmHandler(alarms=[alarm for alarm in alarm_mapper.generate_alarms()])
    # telemetry = [
    #     alarm_handler.assign_alarm_to_telemetry(telemetry).as_dict()
    #     for telemetry in telemetry_mapper.generate_telemetry_samples()
    # ]
        
    df_alarms = df_alarms_chunk_generator.drop(['registration'], axis=1)
    df_top_alarms = df_alarms.iloc[0].sort_values(ascending=False, na_position='last')[:int(top)]
    df_result = df_top_alarms.to_dict()
    df_result['total'] = int(np.sum(df_top_alarms))
    df_result['pilot'] = pilot_id
    return  [df_result]

def get_flightswithalarms_by_pilot_id(
    connection: ConnectionParamsHandler, 
    pilot_id: str,
    start_date: str,
    end_date: str
):
    """
    Retrieves all alarms from the database for the given registration_id.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.
    pilot_id : str
        The pilot_id to filter by.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a telemetry sample, containing the telemetry point information and the alarms raised at that point.
    """
    pilot_id = pilot_id.strip()
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )

    # alarm_getter = AlarmDBAccess(manager=db_manager)
    # df_alarm_chunk_generator=alarm_getter.get_alarm_by_marca(marca=registration_id)
    # alarm_mapper = AlarmMapper(df_chunk_generator=df_alarm_chunk_generator)
    telemetry_getter = PilotTelemetryMQTTDatabaseAccess(manager=db_manager)
    
    df_alarms_chunk_generator=telemetry_getter.get_flightswithalarms_by_pilot_datetime_interval(pilot=pilot_id,
                                                                                     start_datetime=start_date,
                                                                                     end_datetime=end_date
                                                                                     ) 
    if df_alarms_chunk_generator.dropna(how='all').empty:
        return []
    # telemetry_mapper = UnformattedTelemetryMapper(df_chunk_generator=telemetry_getter.get_telemetry_by_marca_unformatted(marca=registration_id), position_assigner=position_assigner)

    # telemetry_mapper = FormattedTelemetryMapper(df_chunk_generator=df_chunk_generator,position_assigner=position_assigner)
    # alarm_handler = AlarmHandler(alarms=[alarm for alarm in alarm_mapper.generate_alarms()])
    # telemetry = [
    #     alarm_handler.assign_alarm_to_telemetry(telemetry).as_dict()
    #     for telemetry in telemetry_mapper.generate_telemetry_samples()
    # ]
    return [int(df_alarms_chunk_generator['numberoflights'][0])]


def get_top_flightswithalarms_by_pilot_id(
    connection: ConnectionParamsHandler, 
    pilot_id: str,
    top:str,
    start_date: str,
    end_date: str
):
    """
    Retrieves all alarms from the database for the given pilot_id.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.
    pilot_id : str
        The pilot_id to filter by.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a telemetry sample, containing the telemetry point information and the alarms raised at that point.
    """
    pilot_id = pilot_id.strip()
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )

    # alarm_getter = AlarmDBAccess(manager=db_manager)
    # df_alarm_chunk_generator=alarm_getter.get_alarm_by_marca(marca=registration_id)
    # alarm_mapper = AlarmMapper(df_chunk_generator=df_alarm_chunk_generator)
    telemetry_getter = PilotTelemetryMQTTDatabaseAccess(manager=db_manager)
    
    df_alarms_chunk_generator=telemetry_getter.get_top_flightswithalarms_by_pilot_datetime_interval(pilot=pilot_id,
                                                                                                    top=top,
                                                                                                    start_datetime=start_date,
                                                                                                    end_datetime=end_date
                                                                                                    ) 
    
    if df_alarms_chunk_generator.dropna(how='all').empty:
        return []
    # telemetry_mapper = UnformattedTelemetryMapper(df_chunk_generator=telemetry_getter.get_telemetry_by_marca_unformatted(marca=registration_id), position_assigner=position_assigner)

    # telemetry_mapper = FormattedTelemetryMapper(df_chunk_generator=df_chunk_generator,position_assigner=position_assigner)
    # alarm_handler = AlarmHandler(alarms=[alarm for alarm in alarm_mapper.generate_alarms()])
    # telemetry = [
    #     alarm_handler.assign_alarm_to_telemetry(telemetry).as_dict()
    #     for telemetry in telemetry_mapper.generate_telemetry_samples()
    # ]
    df_alarms_chunk_generator = df_alarms_chunk_generator.dropna(axis=1, how='all')
    return df_alarms_chunk_generator.to_dict(orient='records')

def get_flight_alarms_by_flight_id(connection: ConnectionParamsHandler, flight_id: int):
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )

    telemetry_getter = PilotTelemetryMQTTDatabaseAccess(manager=db_manager)
    # telemetry_mapper = UnformattedTelemetryMapper(df_chunk_generator=telemetry_getter.get_telemetry_by_marca_datetime_interval_unformatted(marca=flight.registration_id,
    #                                                                                                                 start_datetime=flight.stick_on,
    #                                                                                                                 end_datetime=flight.stick_off),
    #                                    position_assigner=position_assigner)
    
    
    # df_chunk_generator=telemetry_getter.get_alarms_by_marca_datetime_interval(
    #         marca=flight.registration_id,
    #         start_datetime=flight.stick_on,
    #         end_datetime=flight.stick_off,
    #     )
    
    df_chunk_generator=telemetry_getter.get_alarms_by_flight(id_volo=flight_id)
    
    if df_chunk_generator.dropna(how='all').empty:
        return []
    # telemetry_mapper = FormattedTelemetryMapper(
    #     df_chunk_generator = df_chunk_generator,
    #     position_assigner=position_assigner,
    # )
    # alarm_getter = AlarmDBAccess(manager=db_manager)
    # alarm_mapper = AlarmMapper(
    #     df_chunk_generator=alarm_getter.get_alarm_by_marca(
    #         marca=flight.registration_id.strip()
    #     )
    # )
    # alarm_handler = AlarmHandler(
    #     alarms=[alarm for alarm in alarm_mapper.generate_alarms()] 
    # )
    # telemetry: list = [
    #     alarm_handler.assign_alarm_to_telemetry(telemetry_sample)
    #     for telemetry_sample in telemetry_mapper.generate_telemetry_samples()
    # ]
    # alarm_telemetry: list = [
    #     telemetry_sample.as_dict()
    #     for telemetry_sample in telemetry
    #     if telemetry_sample.has_alarms()
    # ]
    df_chunk_generator['total'] = df_chunk_generator.drop(['registration'], axis=1).sum(axis=1)
    df_chunk_generator = df_chunk_generator.dropna(axis=1, how='all')
    return df_chunk_generator.to_dict(orient='records')


def get_top_flight_alarms_by_flight_id(connection: ConnectionParamsHandler, flight_id: int, top: int):
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )

    flight_getter = PilotFlightDBAccess(manager=db_manager)
    df_chunk_generator = flight_getter.get_flight_by_id(id_volo=flight_id)
    if df_chunk_generator.dropna(how='all').empty:
        return []
    flight_mapper = FlightMapper(df_chunk_generator=df_chunk_generator)

    try:
        flight = flight_mapper.generate_converted_flights()[0]
    except IndexError:
        return []

    telemetry_getter = PilotTelemetryMQTTDatabaseAccess(manager=db_manager)
    # telemetry_mapper = UnformattedTelemetryMapper(df_chunk_generator=telemetry_getter.get_telemetry_by_marca_datetime_interval_unformatted(marca=flight.registration_id,
    #                                                                                                                 start_datetime=flight.stick_on,
    #                                                                                                                 end_datetime=flight.stick_off),
    #                                    position_assigner=position_assigner)
    
    
    df_chunk_generator=telemetry_getter.get_alarms_by_marca_datetime_interval(
            marca=flight.registration_id,
            start_datetime=flight.stick_on,
            end_datetime=flight.stick_off,
        )
    
    if df_chunk_generator.dropna(how='all').empty:
        return []
    # telemetry_mapper = FormattedTelemetryMapper(
    #     df_chunk_generator = df_chunk_generator,
    #     position_assigner=position_assigner,
    # )
    # alarm_getter = AlarmDBAccess(manager=db_manager)
    # alarm_mapper = AlarmMapper(
    #     df_chunk_generator=alarm_getter.get_alarm_by_marca(
    #         marca=flight.registration_id.strip()
    #     )
    # )
    # alarm_handler = AlarmHandler(
    #     alarms=[alarm for alarm in alarm_mapper.generate_alarms()]
    # )
    # telemetry: list = [
    #     alarm_handler.assign_alarm_to_telemetry(telemetry_sample)
    #     for telemetry_sample in telemetry_mapper.generate_telemetry_samples()
    # ]
    # alarm_telemetry: list = [
    #     telemetry_sample.as_dict()
    #     for telemetry_sample in telemetry
    #     if telemetry_sample.has_alarms()
    # ]
    df_alarms = df_chunk_generator.drop(['registration'], axis=1)
    df_top_alarms = df_alarms.iloc[0].sort_values(ascending=False, na_position='last')[:int(top)]
    df_result = df_top_alarms.to_dict()
    df_result['total'] = int(np.sum(df_top_alarms))
    df_result['registration'] = flight.registration_id
    return  [df_result]

def get_all_recent_alarms_telemetry(
    connection: ConnectionParamsHandler, start_date: str, end_date: str
):
    """
    Retrieves all telemetry with alarms from the database for all registrations in the given time range.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        The database connection parameters.
    start_date : str
        The start of the time range in ISO 8601 format.
    end_date : str
        The end of the time range in ISO 8601 format.

    Returns
    -------
    list[dict]: A list of dictionaries, each representing a telemetry sample, containing the telemetry point information and the alarms raised at that point.
    """
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )

    telemetry_getter = PilotTelemetryMQTTDatabaseAccess(manager=db_manager)
    alarm_getter = AlarmDBAccess(manager=db_manager)
    registration_getter = AirplaneInfoDBAccess(manager=db_manager)
    # registration_mapper = AirplaneInfoMapper(
    #     df_chunk_generator=registration_getter.get_all_airplane_with_flights_info()
    # )
    
    # registration_ids = [
    #     registration.id
    #     for registration in registration_mapper.generate_airplane_datasheets()
    # ] 
    
    df_chunk_generator=registration_getter.get_all_airplane_with_flights_info()
    registration_ids = df_chunk_generator['marche'].tolist()
    
    # telemetries = []
    # for registration_id in registration_ids:
    #     registration_id = registration_id.strip()
    #     df_chunk_generator = telemetry_getter.get_telemetry_alarms_by_marca_datetime_interval(
    #             marca=registration_id, start_datetime=start_date, end_datetime=end_date
    #         )
    #     if df_chunk_generator.dropna(how='all').empty:
    #         telemetry_reg = []
    #     else:
    #         telemetry_mapper = FormattedTelemetryMapper(
    #             df_chunk_generator=df_chunk_generator,
    #             position_assigner=position_assigner
    #         )
    #         telemetry_reg = [
    #             telemetry_sample
    #             for telemetry_sample in telemetry_mapper.generate_telemetry_samples()
    #         ]
    #     telemetries.extend(telemetry_reg)   
        
    # alarm_mapper = AlarmMapper(df_chunk_generator=alarm_getter.get_all_alarms())

    # alarm_handler = AlarmHandler(
    #     alarms=[alarm for alarm in alarm_mapper.generate_alarms()]
    # )

    # telemetry = [
    #     alarm_handler.assign_alarm_to_telemetry(telemetry_sample)
    #     for telemetry_sample in telemetries
    # ]
    # alarm_telemetry = [
    #     telemetry_sample.as_dict()
    #     for telemetry_sample in telemetry 
    #     if telemetry_sample.has_alarms()
    # ]
    
    if len(registration_ids) > 1:
        registration_ids = (registration_id.strip() for registration_id in registration_ids)
        df_alarms_chunk_generator = telemetry_getter.get_telemetry_alarms_by_mutiple_marcas_datetime_interval(
                marcas=registration_ids, start_datetime=start_date, end_datetime=end_date
            )
        
    else:
        df_alarms_chunk_generator = telemetry_getter.get_telemetry_alarms_by_marca_datetime_interval(
                marca=registration_ids[0].strip(), start_datetime=start_date, end_datetime=end_date
            )
    
    if df_alarms_chunk_generator.dropna(how='all').empty:
        return []
        
    telemetry_mapper = FormattedTelemetryMapper(
        df_chunk_generator=df_alarms_chunk_generator,
        position_assigner=position_assigner
    )
    
    telemetry_alarms_samples = telemetry_mapper.generate_telemetry_alarms(has_alarms=True) # (has_alarms=True) # generate_telemetry_alarms(has_alarms=True)
    # telemetry_alarms_samples = telemetry_alarms_samples.apply(lambda x: x.as_dict())
    
    
    # alarm_mapper = AlarmMapper(df_chunk_generator=alarm_getter.get_all_alarms())

    # alarm_handler = AlarmHandler(
    #     alarms=[alarm for alarm in alarm_mapper.generate_alarms()]
    # )

    # telemetry = [
    #     alarm_handler.assign_alarm_to_telemetry(telemetry_sample)
    #     for telemetry_sample in telemetry_mapper.generate_telemetry_samples()
    # ]
    # alarm_telemetry = [
    #     telemetry_sample.as_dict()
    #     for telemetry_sample in telemetry
    #     if telemetry_sample.has_alarms()
    # ]
    # return alarm_telemetry
    # list(map(lambda telemetry: telemetry.as_dict(), telemetry_alarms_samples)) 
    
    # df_alarms_chunk_generator.drop('date_time', axis=1, inplace=True) 
    return [tel.as_dict() for tel in telemetry_alarms_samples] # telemetry_alarms_samples.tolist()


def get_all_recent_alarms_telemetry_by_id(
    connection: ConnectionParamsHandler,
    start_date: str,
    end_date: str,
    registration_ids: list[str],
):
    """
    Retrieves all telemetry with alarms for the given registration and time range.

    Parameters:
    - connection (ConnectionParamsHandler): The database connection parameters.
    - start_date (str): The start of the time range in ISO 8601 format.
    - end_date (str): The end of the time range in ISO 8601 format.
    - registration_id (str): The registration id to filter by.

    Returns:
    - list[dict]: A list of dictionaries, each representing a telemetry sample, containing the telemetry point information and the alarms raised at that point.
    """
    
        
    db_manager = DatabaseManager(
            username=connection.username,
            password=connection.password,
            ip_address=connection.ip_address,
            port=connection.port,
            db_name=connection.db_name,
        )

    telemetry_getter = PilotTelemetryMQTTDatabaseAccess(manager=db_manager)
    # alarm_getter = AlarmDBAccess(manager=db_manager)

    # telemetry_mapper = UnformattedTelemetryMapper(df_chunk_generator=telemetry_getter.get_telemetry_by_marca_datetime_interval_unformatted(start_datetime=start_date,
    #                                                                                                           end_datetime=end_date,
    #                                                                                                           marca=registration_id),
    #                                    position_assigner=position_assigner)
    
    if len(registration_ids) > 1:
        registration_ids = (registration_id.strip() for registration_id in registration_ids)
        df_chunk_generator = telemetry_getter.get_telemetry_alarms_by_mutiple_marcas_datetime_interval(
                marcas=registration_ids, start_datetime=start_date, end_datetime=end_date
            )
        
    else:
        df_chunk_generator = telemetry_getter.get_telemetry_alarms_by_marca_datetime_interval(
                marca=registration_ids[0].strip(), start_datetime=start_date, end_datetime=end_date
            )

    if df_chunk_generator.dropna(how='all').empty:
        return []
    telemetry_mapper = FormattedTelemetryMapper(
        df_chunk_generator=df_chunk_generator,
        position_assigner=position_assigner,
    )
    
    telemetry_alarms_samples = telemetry_mapper.generate_telemetry_alarms(has_alarms=True) # (has_alarms=True)

    # alarm_mapper = AlarmMapper(df_chunk_generator=alarm_getter.get_all_alarms())

    # alarm_handler = AlarmHandler(
    #     alarms=[alarm for alarm in alarm_mapper.generate_alarms()]
    # )

    # telemetry: list = [
    #     alarm_handler.assign_alarm_to_telemetry(telemetry_sample)
    #     for telemetry_sample in telemetry_mapper.generate_telemetry_samples()
    # ]
    # alarm_telemetry: list = [
    #     telemetry_sample.as_dict()
    #     for telemetry_sample in telemetry
    #     if telemetry_sample.has_alarms()
    # ]
    # telemetry_alarms_samples = telemetry_mapper.new_generate_telemetry_samples()
    # alarm_mapping = {
    #     'alarm_g_tot': 'g_tot',
    #     'alarm_ground_speed': 'ground_speed',
    #     'alarm_vertical_speed': 'vertical_speed',
    #     'alarm_pitch': 'pitch',
    #     'alarm_roll': 'roll',
    #     'alarm_altitude': 'altitude',
    #     'alarm_high_roll_at_low_height': 'high_roll_at_low_height',
    #     'alarm_low_ground_speed_at_low_height_with_low_acceleration':'low_ground_speed_at_low_height_with_low_acceleration',
    #     'alarm_high_pitch_at_low_height_with_low_acceleration': 'high_pitch_at_low_height_with_low_acceleration'
    # }

    # # Function to merge alarms into a single list
    # def merge_alarms(row):
    #     return [alarm_mapping[col] for col in alarm_mapping if row[col] == 1]

    # # Create the new alarms column
    # telemetry_alarms_samples['alarms'] = df_chunk_generator.apply(merge_alarms, axis=1)
    # telemetry_alarms_samples['date_time'] = telemetry_alarms_samples['date_time'].astype(str)
    # telemetry_alarms_samples = telemetry_alarms_samples[telemetry_alarms_samples['alarms'].apply(lambda x: len(x)!=0)]
    # telemetry_alarms_samples = telemetry_alarms_samples.dropna(axis=1, how='all')
    # return telemetry_alarms_samples.to_dict(orient="records")
    return list(map(lambda telemetry: telemetry.as_dict(), telemetry_alarms_samples))#[telemetry.as_dict() for telemetry in telemetry_alarms_samples]
