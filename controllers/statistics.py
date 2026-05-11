import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any
from db_connection_params_handler import ConnectionParamsHandler
from db_handlers.ibm_db2.MQTT_db_access import TelemetryMQTTDatabaseAccess
from db_handlers.ibm_db2.airplane_info_db_access import AirplaneInfoDBAccess
from db_factory import make_db_manager


def get_all_recent_alarms(connection: ConnectionParamsHandler, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    db_manager = make_db_manager(connection)

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

    if not valid_dfs:
        return []

    df_chunk_generator = pd.concat(valid_dfs, ignore_index=True)

    if df_chunk_generator.dropna(how='all').empty:
        return []

    df_chunk_generator['total'] = df_chunk_generator.drop(['registration'], axis=1).apply(lambda row: row.sum(), axis=1)
    df_chunk_generator_sorted = df_chunk_generator.sort_values(by='total', ascending=False)
    return df_chunk_generator_sorted.to_dict(orient='records')


def get_all_recent_alarms_pre(connection: ConnectionParamsHandler, start_date: str, end_date: str):
    db_manager = make_db_manager(connection)

    registration_getter = AirplaneInfoDBAccess(manager=db_manager)
    df_registrations = registration_getter.get_all_airplane_with_flights_info()
    registration_ids = tuple(df_registrations["marche"].tolist())

    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)

    if len(registration_ids) > 1:
        df_chunk_generator = telemetry_getter.get_alarms_by_mutiple_marcas_datetime_interval(
            marcas=registration_ids, start_datetime=start_date, end_datetime=end_date
        )
    else:
        df_chunk_generator = telemetry_getter.get_alarms_by_marca_datetime_interval(
            marca=registration_ids[0].strip(), start_datetime=start_date, end_datetime=end_date
        )

    if df_chunk_generator.dropna(how='all').empty:
        return []

    df_chunk_generator['total'] = df_chunk_generator.drop(['registration'], axis=1).apply(lambda row: row.sum(), axis=1)
    df_chunk_generator_sorted = df_chunk_generator.sort_values(by='total', ascending=False)
    return df_chunk_generator_sorted.to_dict(orient='records')
