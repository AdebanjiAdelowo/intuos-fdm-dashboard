# import datetime
import time
import asyncio
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
import numpy as np
from db_connection_params_handler import ConnectionParamsHandler
from db_handlers.ibm_db2.MQTT_db_access import TelemetryMQTTDatabaseAccess
from db_handlers.ibm_db2.airplane_info_db_access import AirplaneInfoDBAccess
from db_handlers.ibm_db2.alarm_db_access import AlarmDBAccess
from db_handlers.ibm_db2.db_query_manager import DatabaseManager
from db_handlers.ibm_db2.flight_db_access import FlightDBAccess
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

    flight_getter = FlightDBAccess(manager=db_manager)
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

    flight_getter = FlightDBAccess(manager=db_manager)
    df_chunk_generator=flight_getter.get_flight_by_id(id_volo=id)
    if df_chunk_generator.dropna(how='all').empty:
        return []
    flight_mapper = FlightMapper(df_chunk_generator=df_chunk_generator)

    try:
        flight = flight_mapper.generate_converted_flights().iloc[0]
    except IndexError:
        return []

    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
    
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

async def get_telemetry_async_threaded(
            registration_ids: List[str], 
            start_date: str, 
            end_date: str, 
            telemetry_getter
        ):
    """
    Use this for synchronous telemetry database calls that need to be made concurrent
    """
    def fetch_telemetry_sync(reg_id: str):
        return telemetry_getter.get_telemetry_by_marca_datetime_interval(
            marca=reg_id.strip(), 
            start_datetime=start_date, 
            end_datetime=end_date
        )
    
    # Create a thread pool executor
    with ThreadPoolExecutor(max_workers=10) as executor:
        loop = asyncio.get_event_loop()
        
        # Submit all tasks to the thread pool
        tasks = [
            loop.run_in_executor(executor, fetch_telemetry_sync, reg_id)
            for reg_id in registration_ids
        ]
        
        # Wait for all tasks to complete
        list_dfs = await asyncio.gather(*tasks)
    
    # Filter out empty results and combine dataframes
    valid_dfs = [df for df in list_dfs if df is not None and not df.empty]
    
    if valid_dfs:
        df_chunk_generator = pd.concat(valid_dfs, ignore_index=True)
        return df_chunk_generator
    else:
        return pd.DataFrame()
    

async def get_flight_telemetry_by_date_range_async(
            connection: ConnectionParamsHandler,
            registration_ids: List[str],
            start_date: str,
            end_date: str,
        ) -> List[Dict[str, Any]]:
    """
    Retrieves all the telemetry samples for given registration ids in the given time range, 
    assigns alarms to the telemetry points, and returns the telemetry samples as a list of dictionaries.

    Args:
        connection (ConnectionParamsHandler): The database connection parameters.
        registration_ids (List[str]): The list of registration IDs.
        start_date (str): The start of the time range in ISO 8601 format.
        end_date (str): The end of the time range in ISO 8601 format.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries, each representing a telemetry sample, 
                              containing the telemetry point information and the alarms raised at that point.
    """
    try:
        db_manager = DatabaseManager(
            username=connection.username,
            password=connection.password,
            ip_address=connection.ip_address,
            port=connection.port,
            db_name=connection.db_name,
        )

        telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
        
        # print(f"🚀 Processing telemetry for {len(registration_ids)} registrations from {start_date} to {end_date}")
        
        # Handle different scenarios based on number of registrations
        if len(registration_ids) == 1:
            # Single registration - use direct method
            df_chunk_generator = telemetry_getter.get_telemetry_by_marca_datetime_interval(
                marca=registration_ids[0].strip(), 
                start_datetime=start_date, 
                end_datetime=end_date
            )
        elif len(registration_ids) <= 8:
            # Small number - use async for better performance
            registration_ids_cleaned = [reg_id.strip() for reg_id in registration_ids]
            df_chunk_generator = await get_telemetry_async_threaded(
                registration_ids_cleaned, start_date, end_date, telemetry_getter
            )
        else:
            # Large number - process in batches
            batch_size = 5  # Smaller batch size for telemetry data (potentially larger datasets)
            all_dfs = []
            
            registration_ids_cleaned = [reg_id.strip() for reg_id in registration_ids]
            
            for i in range(0, len(registration_ids_cleaned), batch_size):
                batch = registration_ids_cleaned[i:i + batch_size]
                # print(f"📦 Processing telemetry batch {i//batch_size + 1}/{(len(registration_ids_cleaned)-1)//batch_size + 1}")
                
                batch_df = await get_telemetry_async_threaded(
                    batch, start_date, end_date, telemetry_getter
                )
                
                if not batch_df.empty:
                    all_dfs.append(batch_df)
                
                # Small delay between batches to avoid overwhelming the database
                await asyncio.sleep(0.2)  # Slightly longer delay for telemetry data
            
            if all_dfs:
                df_chunk_generator = pd.concat(all_dfs, ignore_index=True)
            else:
                df_chunk_generator = pd.DataFrame()
        
        # Check if we have any telemetry data
        if df_chunk_generator is None or df_chunk_generator.dropna(how='all').empty:
            # print("ℹ️  No telemetry data found for the specified time range")
            return []
        
        # print(f"📊 Processing {len(df_chunk_generator)} telemetry records...")
        
        # Create telemetry mapper and generate telemetry objects
        telemetry_mapper = FormattedTelemetryMapper(
            df_chunk_generator=df_chunk_generator,
            position_assigner=position_assigner
        )

        telemetry_objects = telemetry_mapper.generate_telemetry_alarms(has_alarms=True)
        result = list(map(lambda telemetry: telemetry.as_dict(), telemetry_objects))
        
        # print(f"✅ Successfully processed {len(result)} telemetry objects")
        return result
        
    except Exception as e:
        # print(f"❌ Error in get_flight_telemetry_by_date_range: {str(e)}")
        raise

def get_telemetry_threaded(
    registration_ids: List[str], 
    start_date: str, 
    end_date: str, 
    telemetry_getter
):
    """
    Synchronously retrieves telemetry data concurrently using threads.
    """
    def fetch_telemetry_sync(reg_id: str):
        return telemetry_getter.get_telemetry_by_marca_datetime_interval(
            marca=reg_id.strip(), 
            start_datetime=start_date, 
            end_datetime=end_date
        )
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_telemetry_sync, reg_id) for reg_id in registration_ids]
        list_dfs = [f.result() for f in futures]

    valid_dfs = [df for df in list_dfs if df is not None and not df.empty]

    if valid_dfs:
        return pd.concat(valid_dfs, ignore_index=True)
    else:
        return pd.DataFrame()

def get_flight_telemetry_by_date_range_sync(
    connection: ConnectionParamsHandler,
    registration_ids: List[str],
    start_date: str,
    end_date: str,
) -> List[Dict[str, Any]]:
    try:
        db_manager = DatabaseManager(
            username=connection.username,
            password=connection.password,
            ip_address=connection.ip_address,
            port=connection.port,
            db_name=connection.db_name,
        )

        telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
        registration_ids_cleaned = [reg_id.strip() for reg_id in registration_ids]

        if len(registration_ids_cleaned) == 1:
            df_chunk_generator = telemetry_getter.get_telemetry_by_marca_datetime_interval(
                marca=registration_ids_cleaned[0], 
                start_datetime=start_date, 
                end_datetime=end_date
            )
        elif len(registration_ids_cleaned) <= 8:
            df_chunk_generator = get_telemetry_threaded(
                registration_ids_cleaned, start_date, end_date, telemetry_getter
            )
        else:
            batch_size = 5
            all_dfs = []

            for i in range(0, len(registration_ids_cleaned), batch_size):
                batch = registration_ids_cleaned[i:i + batch_size]
                batch_df = get_telemetry_threaded(batch, start_date, end_date, telemetry_getter)

                if not batch_df.empty:
                    all_dfs.append(batch_df)

                # Optional: small delay between batches
                time.sleep(0.2)

            df_chunk_generator = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

        if df_chunk_generator is None or df_chunk_generator.dropna(how='all').empty:
            return []

        telemetry_mapper = FormattedTelemetryMapper(
            df_chunk_generator=df_chunk_generator,
            position_assigner=position_assigner
        )

        telemetry_objects = telemetry_mapper.generate_telemetry_alarms(has_alarms=True)
        return [telemetry.as_dict() for telemetry in telemetry_objects]

    except Exception as e:
        raise

    
def get_flight_telemetry_by_date_range_pre(
    connection: ConnectionParamsHandler,
    registration_ids: list[str],
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

    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
    
    if len(registration_ids) > 1:
        registration_ids = [reg_id.strip() for reg_id in registration_ids]
        df_chunk_generator=telemetry_getter.get_telemetry_by_marcas_datetime_interval(
                marcas=registration_ids, start_datetime=start_date, end_datetime=end_date
            )
            
    else:
        df_chunk_generator=telemetry_getter.get_telemetry_by_marca_datetime_interval(
            marca=registration_ids[0].strip(), start_datetime=start_date, end_datetime=end_date
        )
    
    if df_chunk_generator.dropna(how='all').empty:
        return []
    telemetry_mapper = FormattedTelemetryMapper(
        df_chunk_generator=df_chunk_generator,
        position_assigner=position_assigner
    )

    telemetry_objects = telemetry_mapper.generate_telemetry_alarms(has_alarms=True)
    return list(map(lambda telemetry: telemetry.as_dict(), telemetry_objects))



def get_alarms_by_registration_id(
    connection: ConnectionParamsHandler, registration_id: str
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
    registration_id = registration_id.strip()
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
    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
    
    df_alarms_chunk_generator=telemetry_getter.get_alarms_by_marca(marca=registration_id) 
    
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


def get_all_recent_alarms_by_registration_id(
    connection: ConnectionParamsHandler, 
    registration_id: str,
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
    registration_id = registration_id.strip()
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
    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
    
    df_alarms_chunk_generator=telemetry_getter.get_alarms_by_marca_datetime_interval(marca=registration_id,
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


def get_all_top_recent_alarms_by_registration_id(
    connection: ConnectionParamsHandler, 
    registration_id: str,
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
    registration_id = registration_id.strip()
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
    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
    
    df_alarms_chunk_generator=telemetry_getter.get_alarms_by_marca_datetime_interval(marca=registration_id,
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
    df_result['registration'] = registration_id
    return  [df_result]

def get_flightswithalarms_by_registration_id(
    connection: ConnectionParamsHandler, 
    registration_id: str,
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
    registration_id = registration_id.strip()
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
    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
    
    df_alarms_chunk_generator=telemetry_getter.get_flightswithalarms_by_marca_datetime_interval(marca=registration_id,
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


def get_top_flightswithalarms_by_registration_id(
    connection: ConnectionParamsHandler, 
    registration_id: str,
    top:str,
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
    registration_id = registration_id.strip()
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
    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
    
    df_alarms_chunk_generator=telemetry_getter.get_top_flightswithalarms_by_marca_datetime_interval(marca=registration_id,
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

    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
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

    flight_getter = FlightDBAccess(manager=db_manager)
    df_chunk_generator = flight_getter.get_flight_by_id(id_volo=flight_id)
    if df_chunk_generator.dropna(how='all').empty:
        return []
    flight_mapper = FlightMapper(df_chunk_generator=df_chunk_generator)

    try:
        flight = flight_mapper.generate_converted_flights()[0]
    except IndexError:
        return []

    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
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

def get_telemetry_alarms_threaded(
    registration_ids: List[str], 
    start_date: str, 
    end_date: str, 
    telemetry_getter
):
    """
    Synchronously retrieves telemetry alarms concurrently using threads.
    """
    def fetch_alarms(reg_id: str):
        return telemetry_getter.get_telemetry_alarms_by_marca_datetime_interval(
            marca=reg_id.strip(), 
            start_datetime=start_date, 
            end_datetime=end_date
        )
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_alarms, reg_id) for reg_id in registration_ids]
        list_dfs = [f.result() for f in futures]
    
    valid_dfs = [df for df in list_dfs if df is not None and not df.empty]
    return pd.concat(valid_dfs, ignore_index=True) if valid_dfs else pd.DataFrame()


def get_all_recent_alarms_telemetry_sync(
    connection: ConnectionParamsHandler, 
    start_date: str, 
    end_date: str
) -> List[Dict[str, Any]]:
    """
    Retrieves all telemetry alarms from the database synchronously.
    """
    try:
        db_manager = DatabaseManager(
            username=connection.username,
            password=connection.password,
            ip_address=connection.ip_address,
            port=connection.port,
            db_name=connection.db_name,
        )

        telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
        alarm_getter = AlarmDBAccess(manager=db_manager)
        registration_getter = AirplaneInfoDBAccess(manager=db_manager)

        df_registrations = registration_getter.get_all_airplane_with_flights_info()
        
        if df_registrations.empty:
            return []

        registration_ids = df_registrations['marche'].dropna().tolist()
        
        if not registration_ids:
            return []

        registration_ids_cleaned = [reg_id.strip() for reg_id in registration_ids]

        if len(registration_ids_cleaned) == 1:
            df_alarms_chunk_generator = telemetry_getter.get_telemetry_alarms_by_marca_datetime_interval(
                marca=registration_ids_cleaned[0], 
                start_datetime=start_date, 
                end_datetime=end_date
            )
        elif len(registration_ids_cleaned) <= 8:
            df_alarms_chunk_generator = get_telemetry_alarms_threaded(
                registration_ids_cleaned, start_date, end_date, telemetry_getter
            )
        else:
            batch_size = 5
            all_dfs = []
            for i in range(0, len(registration_ids_cleaned), batch_size):
                batch = registration_ids_cleaned[i:i + batch_size]
                batch_df = get_telemetry_alarms_threaded(batch, start_date, end_date, telemetry_getter)

                if not batch_df.empty:
                    all_dfs.append(batch_df)

                time.sleep(0.2)  # Delay to reduce DB load

            df_alarms_chunk_generator = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

        if df_alarms_chunk_generator is None or df_alarms_chunk_generator.dropna(how='all').empty:
            return []

        telemetry_mapper = FormattedTelemetryMapper(
            df_chunk_generator=df_alarms_chunk_generator,
            position_assigner=position_assigner
        )
        
        telemetry_alarms_samples = telemetry_mapper.generate_telemetry_alarms(has_alarms=True)
        return [tel.as_dict() for tel in telemetry_alarms_samples]

    except Exception as e:
        raise

async def get_telemetry_alarms_async_threaded(
    registration_ids: List[str], 
    start_date: str, 
    end_date: str, 
    telemetry_getter
):
    """
    Use this for synchronous telemetry alarms database calls that need to be made concurrent
    """
    def fetch_telemetry_alarms_sync(reg_id: str):
        return telemetry_getter.get_telemetry_alarms_by_marca_datetime_interval(
            marca=reg_id.strip(), 
            start_datetime=start_date, 
            end_datetime=end_date
        )
    
    # Create a thread pool executor
    with ThreadPoolExecutor(max_workers=10) as executor:
        loop = asyncio.get_event_loop()
        
        # Submit all tasks to the thread pool
        tasks = [
            loop.run_in_executor(executor, fetch_telemetry_alarms_sync, reg_id)
            for reg_id in registration_ids
        ]
        
        # Wait for all tasks to complete
        list_dfs = await asyncio.gather(*tasks)
    
    # Filter out empty results and combine dataframes
    valid_dfs = [df for df in list_dfs if df is not None and not df.empty]
    
    if valid_dfs:
        df_chunk_generator = pd.concat(valid_dfs, ignore_index=True)
        return df_chunk_generator
    else:
        return pd.DataFrame()


async def get_all_recent_alarms_telemetry(
    connection: ConnectionParamsHandler, 
    start_date: str, 
    end_date: str
) -> List[Dict[str, Any]]:
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
    List[Dict[str, Any]]: A list of dictionaries, each representing a telemetry sample, 
                          containing the telemetry point information and the alarms raised at that point.
    """
    try:
        db_manager = DatabaseManager(
            username=connection.username,
            password=connection.password,
            ip_address=connection.ip_address,
            port=connection.port,
            db_name=connection.db_name,
        )

        telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
        alarm_getter = AlarmDBAccess(manager=db_manager)
        registration_getter = AirplaneInfoDBAccess(manager=db_manager)

        # print(f"🚀 Retrieving all registrations with flights...")
        df_registrations = registration_getter.get_all_airplane_with_flights_info()
        
        if df_registrations.empty:
            # print("⚠️  No registrations found")
            return []

        registration_ids = df_registrations['marche'].dropna().tolist()
        
        if not registration_ids:
            # print("⚠️  No valid registration IDs found")
            return []

        # print(f"📊 Processing telemetry alarms for {len(registration_ids)} registrations from {start_date} to {end_date}")
        
        # Handle different scenarios based on number of registrations
        if len(registration_ids) == 1:
            # Single registration - use direct method
            df_alarms_chunk_generator = telemetry_getter.get_telemetry_alarms_by_marca_datetime_interval(
                marca=registration_ids[0].strip(), 
                start_datetime=start_date, 
                end_datetime=end_date
            )
        elif len(registration_ids) <= 8:
            # Small number - use async for better performance
            registration_ids_cleaned = [reg_id.strip() for reg_id in registration_ids]
            df_alarms_chunk_generator = await get_telemetry_alarms_async_threaded(
                registration_ids_cleaned, start_date, end_date, telemetry_getter
            )
        else:
            # Large number - process in batches
            batch_size = 5  # Smaller batch size for telemetry alarm data
            all_dfs = []
            
            registration_ids_cleaned = [reg_id.strip() for reg_id in registration_ids]
            
            for i in range(0, len(registration_ids_cleaned), batch_size):
                batch = registration_ids_cleaned[i:i + batch_size]
                # print(f"📦 Processing telemetry alarms batch {i//batch_size + 1}/{(len(registration_ids_cleaned)-1)//batch_size + 1}")
                
                batch_df = await get_telemetry_alarms_async_threaded(
                    batch, start_date, end_date, telemetry_getter
                )
                
                if not batch_df.empty:
                    all_dfs.append(batch_df)
                
                # Small delay between batches to avoid overwhelming the database
                await asyncio.sleep(0.2)
            
            if all_dfs:
                df_alarms_chunk_generator = pd.concat(all_dfs, ignore_index=True)
            else:
                df_alarms_chunk_generator = pd.DataFrame()
        
        # Check if we have any telemetry alarm data
        if df_alarms_chunk_generator is None or df_alarms_chunk_generator.dropna(how='all').empty:
            # print("ℹ️  No telemetry alarm data found for the specified time range")
            return []
        
        # print(f"🔄 Processing {len(df_alarms_chunk_generator)} telemetry alarm records through mapper...")
        
        # Create telemetry mapper and generate telemetry objects
        telemetry_mapper = FormattedTelemetryMapper(
            df_chunk_generator=df_alarms_chunk_generator,
            position_assigner=position_assigner
        )
        
        telemetry_alarms_samples = telemetry_mapper.generate_telemetry_alarms(has_alarms=True)
        result = [tel.as_dict() for tel in telemetry_alarms_samples]
        
        # print(f"✅ Successfully processed {len(result)} telemetry alarm objects")
        return result
        
    except Exception as e:
        # print(f"❌ Error in get_all_recent_alarms_telemetry: {str(e)}")
        raise

def get_all_recent_alarms_telemetry_pre(
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

    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
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
        
        # list_dfs = []
        # for reg_id in registration_ids:
        #     df = telemetry_getter.get_telemetry_alarms_by_marca_datetime_interval(
        #                     marca=reg_id.strip(), start_datetime=start_date, end_datetime=end_date
        #                 )
        #     list_dfs.append(df) 
        # df_alarms_chunk_generator = pd.concat(list_dfs, ignore_index=True)
        
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

async def get_telemetry_alarms_by_ids_async_threaded(
    registration_ids: List[str], 
    start_date: str, 
    end_date: str, 
    telemetry_getter
):
    """
    Use this for synchronous telemetry alarms database calls that need to be made concurrent
    """
    def fetch_telemetry_alarms_sync(reg_id: str):
        return telemetry_getter.get_telemetry_alarms_by_marca_datetime_interval(
            marca=reg_id.strip(), 
            start_datetime=start_date, 
            end_datetime=end_date
        )
    
    # Create a thread pool executor
    with ThreadPoolExecutor(max_workers=10) as executor:
        loop = asyncio.get_event_loop()
        
        # Submit all tasks to the thread pool
        tasks = [
            loop.run_in_executor(executor, fetch_telemetry_alarms_sync, reg_id)
            for reg_id in registration_ids
        ]
        
        # Wait for all tasks to complete
        list_dfs = await asyncio.gather(*tasks)
    
    # Filter out empty results and combine dataframes
    valid_dfs = [df for df in list_dfs if df is not None and not df.empty]
    
    if valid_dfs:
        df_chunk_generator = pd.concat(valid_dfs, ignore_index=True)
        return df_chunk_generator
    else:
        return pd.DataFrame()


async def get_all_recent_alarms_telemetry_by_id(
    connection: ConnectionParamsHandler,
    start_date: str,
    end_date: str,
    registration_ids: List[str],
) -> List[Dict[str, Any]]:
    """
    Retrieves all telemetry with alarms for the given registrations and time range.

    Parameters:
    - connection (ConnectionParamsHandler): The database connection parameters.
    - start_date (str): The start of the time range in ISO 8601 format.
    - end_date (str): The end of the time range in ISO 8601 format.
    - registration_ids (List[str]): The list of registration ids to filter by.

    Returns:
    - List[Dict[str, Any]]: A list of dictionaries, each representing a telemetry sample, 
                            containing the telemetry point information and the alarms raised at that point.
    """
    try:
        db_manager = DatabaseManager(
            username=connection.username,
            password=connection.password,
            ip_address=connection.ip_address,
            port=connection.port,
            db_name=connection.db_name,
        )

        telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
        
        if not registration_ids:
            # print("⚠️  No registration IDs provided")
            return []

        # print(f"🚀 Processing telemetry alarms for {len(registration_ids)} registrations from {start_date} to {end_date}")
        
        # Handle different scenarios based on number of registrations
        if len(registration_ids) == 1:
            # Single registration - use direct method
            df_chunk_generator = telemetry_getter.get_telemetry_alarms_by_marca_datetime_interval(
                marca=registration_ids[0].strip(), 
                start_datetime=start_date, 
                end_datetime=end_date
            )
        elif len(registration_ids) <= 8:
            # Small number - use async for better performance
            registration_ids_cleaned = [reg_id.strip() for reg_id in registration_ids]
            df_chunk_generator = await get_telemetry_alarms_by_ids_async_threaded(
                registration_ids_cleaned, start_date, end_date, telemetry_getter
            )
        else:
            # Large number - process in batches
            batch_size = 5  # Smaller batch size for telemetry alarm data
            all_dfs = []
            
            registration_ids_cleaned = [reg_id.strip() for reg_id in registration_ids]
            
            for i in range(0, len(registration_ids_cleaned), batch_size):
                batch = registration_ids_cleaned[i:i + batch_size]
                # print(f"📦 Processing telemetry alarms batch {i//batch_size + 1}/{(len(registration_ids_cleaned)-1)//batch_size + 1}")
                
                batch_df = await get_telemetry_alarms_by_ids_async_threaded(
                    batch, start_date, end_date, telemetry_getter
                )
                
                if not batch_df.empty:
                    all_dfs.append(batch_df)
                
                # Small delay between batches to avoid overwhelming the database
                await asyncio.sleep(0.2)
            
            if all_dfs:
                df_chunk_generator = pd.concat(all_dfs, ignore_index=True)
            else:
                df_chunk_generator = pd.DataFrame()
        
        # Check if we have any telemetry alarm data
        if df_chunk_generator is None or df_chunk_generator.dropna(how='all').empty:
            # print("ℹ️  No telemetry alarm data found for the specified registrations and time range")
            return []
        
        # print(f"🔄 Processing {len(df_chunk_generator)} telemetry alarm records through mapper...")
        
        # Create telemetry mapper and generate telemetry objects
        telemetry_mapper = FormattedTelemetryMapper(
            df_chunk_generator=df_chunk_generator,
            position_assigner=position_assigner,
        )
        
        telemetry_alarms_samples = telemetry_mapper.generate_telemetry_alarms(has_alarms=True)
        result = list(map(lambda telemetry: telemetry.as_dict(), telemetry_alarms_samples))
        
        # print(f"✅ Successfully processed {len(result)} telemetry alarm objects")
        return result
        
    except Exception as e:
        # print(f"❌ Error in get_all_recent_alarms_telemetry_by_id: {str(e)}")
        raise

def get_all_recent_alarms_telemetry_by_id_pre(
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

    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
    # alarm_getter = AlarmDBAccess(manager=db_manager)

    # telemetry_mapper = UnformattedTelemetryMapper(df_chunk_generator=telemetry_getter.get_telemetry_by_marca_datetime_interval_unformatted(start_datetime=start_date,
    #                                                                                                           end_datetime=end_date,
    #                                                                                                           marca=registration_id),
    #                                    position_assigner=position_assigner)
    
    if len(registration_ids) > 1:
        list_dfs = []
        for reg_id in registration_ids:
            df = telemetry_getter.get_telemetry_alarms_by_marca_datetime_interval(
                            marca=reg_id.strip(), start_datetime=start_date, end_datetime=end_date
                        )
            list_dfs.append(df) 
        df_chunk_generator = pd.concat(list_dfs, ignore_index=True)
        
        # registration_ids = (registration_id.strip() for registration_id in registration_ids)
        # df_chunk_generator = telemetry_getter.get_telemetry_alarms_by_mutiple_marcas_datetime_interval(
        #         marcas=registration_ids, start_datetime=start_date, end_datetime=end_date
        #     )
        
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


def get_telemetry_alarms_by_ids_threaded(
    registration_ids: List[str],
    start_date: str,
    end_date: str,
    telemetry_getter
) -> pd.DataFrame:
    """
    Retrieves telemetry alarm data concurrently for a list of registration IDs using threads.

    Parameters
    ----------
    registration_ids : List[str]
        A list of aircraft registration identifiers to query telemetry alarms for.
    start_date : str
        The start datetime in ISO 8601 format (e.g., "2024-12-01T00:00:00").
    end_date : str
        The end datetime in ISO 8601 format (e.g., "2024-12-02T00:00:00").
    telemetry_getter : TelemetryMQTTDatabaseAccess
        An object that provides telemetry alarm data retrieval.

    Returns
    -------
    pd.DataFrame
        A concatenated DataFrame containing all telemetry alarms.
        Returns an empty DataFrame if no data is found.
    """
    def fetch_telemetry_alarms_sync(reg_id: str):
        return telemetry_getter.get_telemetry_alarms_by_marca_datetime_interval(
            marca=reg_id.strip(),
            start_datetime=start_date,
            end_datetime=end_date
        )

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(fetch_telemetry_alarms_sync, registration_ids))

    valid_dfs = [df for df in results if df is not None and not df.empty]
    return pd.concat(valid_dfs, ignore_index=True) if valid_dfs else pd.DataFrame()


def get_all_recent_alarms_telemetry_by_id_sync(
    connection: ConnectionParamsHandler,
    start_date: str,
    end_date: str,
    registration_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Retrieves all telemetry alarms for the specified aircraft registration IDs within the given time range.

    Parameters
    ----------
    connection : ConnectionParamsHandler
        Database connection parameters.
    start_date : str
        Start datetime (ISO 8601 format).
    end_date : str
        End datetime (ISO 8601 format).
    registration_ids : List[str]
        Aircraft registration IDs.

    Returns
    -------
    List[Dict[str, Any]]
        List of telemetry alarm dictionaries.
    """
    try:
        db_manager = DatabaseManager(
            username=connection.username,
            password=connection.password,
            ip_address=connection.ip_address,
            port=connection.port,
            db_name=connection.db_name,
        )

        telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)

        if not registration_ids:
            return []

        registration_ids_cleaned = [reg_id.strip() for reg_id in registration_ids]

        if len(registration_ids_cleaned) == 1:
            df_chunk = telemetry_getter.get_telemetry_alarms_by_marca_datetime_interval(
                marca=registration_ids_cleaned[0],
                start_datetime=start_date,
                end_datetime=end_date
            )
        elif len(registration_ids_cleaned) <= 8:
            df_chunk = get_telemetry_alarms_by_ids_threaded(
                registration_ids_cleaned,
                start_date,
                end_date,
                telemetry_getter
            )
        else:
            batch_size = 5
            all_dfs = []

            for i in range(0, len(registration_ids_cleaned), batch_size):
                batch = registration_ids_cleaned[i:i + batch_size]
                batch_df = get_telemetry_alarms_by_ids_threaded(
                    batch,
                    start_date,
                    end_date,
                    telemetry_getter
                )
                if not batch_df.empty:
                    all_dfs.append(batch_df)
                time.sleep(0.2)

            df_chunk = pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()

        if df_chunk is None or df_chunk.dropna(how='all').empty:
            return []

        telemetry_mapper = FormattedTelemetryMapper(
            df_chunk_generator=df_chunk,
            position_assigner=position_assigner
        )

        telemetry_alarms_samples = telemetry_mapper.generate_telemetry_alarms(has_alarms=True)
        return [telemetry.as_dict() for telemetry in telemetry_alarms_samples]

    except Exception as e:
        raise
