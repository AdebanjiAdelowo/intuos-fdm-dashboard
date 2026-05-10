import asyncio
import pandas as pd
from db_connection_params_handler import ConnectionParamsHandler
from db_handlers.ibm_db2.MQTT_db_access import TelemetryMQTTDatabaseAccess
from db_handlers.ibm_db2.airplane_info_db_access import AirplaneInfoDBAccess
from db_handlers.ibm_db2.alarm_db_access import AlarmDBAccess
from db_handlers.ibm_db2.db_query_manager import DatabaseManager
from logic.alarm_assignment import AlarmHandler
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from logic.position_assignment import PositionAssigner
from mappers.airplaneinfo_mapper import AirplaneInfoMapper
from mappers.alarm_mapper import AlarmMapper
from mappers.telemetry_mapper import (
    FormattedTelemetryMapper,
)

position_assigner = PositionAssigner(
    model_file_path="logic/position_assignment_data/f1.pkl",
    label_names_file_path="logic/position_assignment_data/f1_class_names.json",
    features_file_path="logic/position_assignment_data/f1_selected_features.json",
)

async def get_alarms_async_threaded(registration_ids: List[str], start_date: str, end_date: str, telemetry_getter):
    """
    Use this for synchronous database calls that need to be made concurrent
    """
    def fetch_alarms_sync(reg_id: str):
        return telemetry_getter.get_alarms_by_marca_datetime_interval(
            marca=reg_id.strip(), 
            start_datetime=start_date, 
            end_datetime=end_date
        )
    
    # Create a thread pool executor
    with ThreadPoolExecutor(max_workers=10) as executor:
        loop = asyncio.get_event_loop()
        
        # Submit all tasks to the thread pool
        tasks = [
            loop.run_in_executor(executor, fetch_alarms_sync, reg_id)
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
    
    
async def get_all_recent_alarms_async(
                connection: ConnectionParamsHandler, start_date: str, end_date: str
                    ) -> List[Dict[str, Any]]:
    """
    Retrieves all alarms from the database for all registrations in the given time range.

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
    List[Dict[str, Any]]: A list of dictionaries, each representing an alarm counter, 
                          containing the alarm id and the count of how many times it was raised.
    """
    try:
        db_manager = DatabaseManager(
            username=connection.username,
            password=connection.password,
            ip_address=connection.ip_address,
            port=connection.port,
            db_name=connection.db_name,
        )

        registration_getter = AirplaneInfoDBAccess(manager=db_manager)
        df_registrations = registration_getter.get_all_airplane_with_flights_info() 
        
        if df_registrations.empty:
            print("⚠️  No registrations found")
            return []

        registration_ids = df_registrations["marche"].dropna().tolist()
        
        if not registration_ids:
            print("⚠️  No valid registration IDs found")
            return []

        telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
        
        # print(f"🚀 Processing {len(registration_ids)} registrations from {start_date} to {end_date}")
        
        # Handle different scenarios based on number of registrations
        if len(registration_ids) == 1:
            # Single registration - use direct method
            df_chunk_generator = telemetry_getter.get_alarms_by_marca_datetime_interval(
                marca=registration_ids[0].strip(), 
                start_datetime=start_date, 
                end_datetime=end_date
            )
        elif len(registration_ids) <= 8:
            # Small number - use async for better performance
            df_chunk_generator = await get_alarms_async_threaded(
                registration_ids, start_date, end_date, telemetry_getter
            )
        else:
            # Large number - process in batches to avoid overwhelming the database
            batch_size = 10
            all_dfs = []
            
            for i in range(0, len(registration_ids), batch_size):
                batch = registration_ids[i:i + batch_size]
                print(f"📦 Processing batch {i//batch_size + 1}/{(len(registration_ids)-1)//batch_size + 1}")
                
                batch_df = await get_alarms_async_threaded(
                    batch, start_date, end_date, telemetry_getter
                )
                
                if not batch_df.empty:
                    all_dfs.append(batch_df)
                
                # Small delay between batches to avoid overwhelming the database
                await asyncio.sleep(0.1)
            
            if all_dfs:
                df_chunk_generator = pd.concat(all_dfs, ignore_index=True)
            else:
                df_chunk_generator = pd.DataFrame()
        
        # Process results
        if df_chunk_generator is None or df_chunk_generator.dropna(how='all').empty:
            # print("ℹ️  No alarm data found for the specified time range")
            return []
        
        # # Calculate totals and sort
        # alarm_columns = [col for col in df_chunk_generator.columns if col != 'registration']
        # df_chunk_generator = df_chunk_generator[alarm_columns].sum(axis=0)
        # df_chunk_generator['total'] = df_chunk_generator.sum()
        # #df_chunk_generator_sorted = df_chunk_generator.sort_values(by='total', ascending=False)
        
        # # Convert to list of dictionaries
        # # counters = df_chunk_generator_sorted.to_dict(orient='records')
        # counters = df_chunk_generator.to_dict()        
        # print(f"✅ Successfully processed {len(counters)} alarm records")
        # return counters
        
        if df_chunk_generator.dropna(how='all').empty:
            counters = []
        else:
            df_chunk_generator['total'] = df_chunk_generator.drop(['registration'], axis=1).apply(lambda row: row.sum(), axis=1)
            df_chunk_generator_sorted = df_chunk_generator.sort_values(by='total', ascending=False)
            
            counters = df_chunk_generator_sorted.to_dict(orient='records')

            return counters
        
    except Exception as e:
        # print(f"❌ Error in get_all_recent_alarms: {str(e)}")
        raise

def get_all_recent_alarms(connection: ConnectionParamsHandler, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )

    registration_getter = AirplaneInfoDBAccess(manager=db_manager)
    df_registrations = registration_getter.get_all_airplane_with_flights_info() 

    if df_registrations.empty:
        return []

    registration_ids = df_registrations["marche"].dropna().tolist()

    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)

    def fetch_alarms_sync(reg_id: str):
        return telemetry_getter.get_alarms_by_marca_datetime_interval(
            marca=reg_id.strip(), 
            start_datetime=start_date, 
            end_datetime=end_date
        )

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_alarms_sync, reg_id) for reg_id in registration_ids]
        list_dfs = [f.result() for f in futures]

    valid_dfs = [df for df in list_dfs if df is not None and not df.empty]

    if valid_dfs:
        df_chunk_generator = pd.concat(valid_dfs, ignore_index=True)
    else:
        return []

    if df_chunk_generator.dropna(how='all').empty:
        return []

    df_chunk_generator['total'] = df_chunk_generator.drop(['registration'], axis=1).apply(lambda row: row.sum(), axis=1)
    df_chunk_generator_sorted = df_chunk_generator.sort_values(by='total', ascending=False)

    return df_chunk_generator_sorted.to_dict(orient='records')


def get_all_recent_alarms_pre(
    connection: ConnectionParamsHandler, start_date: str, end_date: str
):
    """
    Retrieves all alarms from the database for all registrations in the given time range.

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
    list[dict]: A list of dictionaries, each representing an alarm counter, containing the alarm id and the count of how many times it was raised.
    """

    db_manager = DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )

    registration_getter = AirplaneInfoDBAccess(manager=db_manager)
    df_registrations = registration_getter.get_all_airplane_with_flights_info() 
    # registration_mapper = AirplaneInfoMapper(
    #     df_chunk_generator=df_registrations
    # )

    registration_ids = tuple(df_registrations["marche"].tolist())
    
    # registration_ids = [
    #     registration.id
    #     for registration in registration_mapper.generate_airplane_datasheets()
    # ]

    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
    # alarm_getter = AlarmDBAccess(manager=db_manager)

    # telemetry_mapper = UnformattedTelemetryMapper(
        # df_chunk_generator=telemetry_getter.get_telemetry_by_datetime_interval_unformatted(
        # start_datetime=start_date, end_datetime=end_date),
    #                                    position_assigner=position_assigner
    # )
    if len(registration_ids) > 1:
            # df_chunk_generator = await get_alarms_async_threaded(registration_ids, start_date, end_date, telemetry_getter)

        df_chunk_generator=telemetry_getter.get_alarms_by_mutiple_marcas_datetime_interval(
                marcas=registration_ids, start_datetime=start_date, end_datetime=end_date
            )
        # list_dfs = []
        # for reg_id in registration_ids:
        #     df = telemetry_getter.get_alarms_by_marca_datetime_interval(
        #                     marca=reg_id.strip(), start_datetime=start_date, end_datetime=end_date
        #                 )
        #     list_dfs.append(df)
            
        # df_chunk_generator = pd.concat(list_dfs, ignore_index=True)
    else:
        df_chunk_generator= telemetry_getter.get_alarms_by_marca_datetime_interval(
                marca=registration_ids[0].strip(), start_datetime=start_date, end_datetime=end_date
            )
         
    
    if df_chunk_generator.dropna(how='all').empty:
        counters = []
    else:
        df_chunk_generator['total'] = df_chunk_generator.drop(['registration'], axis=1).apply(lambda row: row.sum(), axis=1)
        df_chunk_generator_sorted = df_chunk_generator.sort_values(by='total', ascending=False)
        
        counters = df_chunk_generator_sorted.to_dict(orient='records')
        
    return counters

        # telemetry_mapper = FormattedTelemetryMapper(
        #     df_chunk_generator=df_chunk_generator,
        #     position_assigner=position_assigner
        # )
        
        # telemetries = [telemetry for telemetry in telemetry_mapper.generate_telemetry_samples()]
      
        # telemetries = []
        
        # for registration_id in registration_ids:
        #     telemetry_mapper = FormattedTelemetryMapper(
        #         df_chunk_generator=telemetry_getter.get_telemetry_alarms_by_marca_datetime_interval(
        #             marca=registration_id, start_datetime=start_date, end_datetime=end_date
        #         ),
        #         position_assigner=position_assigner,
        #     )
        #     telemetries.extend(
        #         [telemetry for telemetry in telemetry_mapper.generate_telemetry_samples()]
        #     )
                
        # alarm_mapper = AlarmMapper(df_chunk_generator=alarm_getter.get_all_alarms())

        # alarm_handler = AlarmHandler(
        #     alarms=[alarm for alarm in alarm_mapper.generate_alarms()]
        # )

        # _ = [
        #     alarm_handler.assign_alarm_to_telemetry(telemetry) for telemetry in telemetries
        # ]
        # counters = [
        #     alarm_counter.as_dict() for alarm_counter in alarm_handler.get_alarm_counters()
        # ]