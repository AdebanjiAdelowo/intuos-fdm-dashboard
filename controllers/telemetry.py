import pandas as pd
from typing import List, Dict, Any
import numpy as np
from db_connection_params_handler import ConnectionParamsHandler
from db_handlers.ibm_db2.MQTT_db_access import TelemetryMQTTDatabaseAccess
from db_handlers.ibm_db2.airplane_info_db_access import AirplaneInfoDBAccess
from db_factory import make_db_manager
from db_handlers.ibm_db2.flight_db_access import FlightDBAccess
from logic.position_assigner_instance import position_assigner
from mappers.flight_mapper import FlightMapper
from mappers.telemetry_mapper import FormattedTelemetryMapper


def get_flight_time_duration(connection: ConnectionParamsHandler, id: int) -> list:
    db_manager = make_db_manager(connection)
    flight_getter = FlightDBAccess(manager=db_manager)
    df_chunk_generator = flight_getter.get_flight_time_duration(id_volo=id)
    if df_chunk_generator.dropna(how='all').empty:
        return []
    df_chunk_generator = df_chunk_generator.dropna(axis=1, how='all')
    return df_chunk_generator.to_dict(orient='records')


def get_flight_telemetry_with_alarms_and_labels(connection: ConnectionParamsHandler, id: int) -> list:
    db_manager = make_db_manager(connection)
    flight_getter = FlightDBAccess(manager=db_manager)
    df_chunk_generator = flight_getter.get_flight_by_id(id_volo=id)
    if df_chunk_generator.dropna(how='all').empty:
        return []
    flight_mapper = FlightMapper(df_chunk_generator=df_chunk_generator)
    try:
        flight = flight_mapper.generate_converted_flights().iloc[0]
    except IndexError:
        return []
    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
    df_chunk_generator = telemetry_getter.get_telemetry_alarms_by_flight(id_volo=id)
    if df_chunk_generator.dropna(how='all').empty:
        return []
    telemetry_alarms_mapper = FormattedTelemetryMapper(
        df_chunk_generator=df_chunk_generator,
        position_assigner=position_assigner,
    )
    telemetry_alarms_samples = telemetry_alarms_mapper.generate_telemetry_alarms()
    return {
        "telemetry_alarms": list(map(lambda telemetry: telemetry.as_dict(), telemetry_alarms_samples)),
        "flight_info": flight.as_dict(),
    }


def get_flight_telemetry_by_date_range_pre(
    connection: ConnectionParamsHandler,
    registration_ids: list[str],
    start_date: str,
    end_date: str,
) -> list[dict]:
    db_manager = make_db_manager(connection)
    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)

    if len(registration_ids) > 1:
        registration_ids = [reg_id.strip() for reg_id in registration_ids]
        df_chunk_generator = telemetry_getter.get_telemetry_by_marcas_datetime_interval(
            marcas=registration_ids, start_datetime=start_date, end_datetime=end_date
        )
    else:
        df_chunk_generator = telemetry_getter.get_telemetry_by_marca_datetime_interval(
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


def get_alarms_by_registration_id(connection: ConnectionParamsHandler, registration_id: str):
    registration_id = registration_id.strip()
    db_manager = make_db_manager(connection)
    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
    df_alarms_chunk_generator = telemetry_getter.get_alarms_by_marca(marca=registration_id)
    if df_alarms_chunk_generator.dropna(how='all').empty:
        return []
    df_alarms_chunk_generator = df_alarms_chunk_generator.dropna(axis=1, how='all')
    return df_alarms_chunk_generator.to_dict(orient='records')


def get_all_recent_alarms_by_registration_id(
    connection: ConnectionParamsHandler,
    registration_id: str,
    start_date: str,
    end_date: str
):
    registration_id = registration_id.strip()
    db_manager = make_db_manager(connection)
    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
    df_alarms_chunk_generator = telemetry_getter.get_alarms_by_marca_datetime_interval(
        marca=registration_id,
        start_datetime=start_date,
        end_datetime=end_date
    )
    if df_alarms_chunk_generator.dropna(how='all').empty:
        return []
    df_alarms_chunk_generator["total"] = df_alarms_chunk_generator.drop(["registration"], axis=1).sum(axis=1)
    df_alarms_chunk_generator = df_alarms_chunk_generator.dropna(axis=1, how='all')
    return df_alarms_chunk_generator.to_dict(orient='records')


def get_all_top_recent_alarms_by_registration_id(
    connection: ConnectionParamsHandler,
    registration_id: str,
    top: str,
    start_date: str,
    end_date: str
):
    registration_id = registration_id.strip()
    db_manager = make_db_manager(connection)
    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
    df_alarms_chunk_generator = telemetry_getter.get_alarms_by_marca_datetime_interval(
        marca=registration_id,
        start_datetime=start_date,
        end_datetime=end_date
    )
    if df_alarms_chunk_generator.dropna(how='all').empty:
        return []
    df_alarms = df_alarms_chunk_generator.drop(['registration'], axis=1)
    df_top_alarms = df_alarms.iloc[0].sort_values(ascending=False, na_position='last')[:int(top)]
    df_result = df_top_alarms.to_dict()
    df_result['total'] = int(np.sum(df_top_alarms))
    df_result['registration'] = registration_id
    return [df_result]


def get_flightswithalarms_by_registration_id(
    connection: ConnectionParamsHandler,
    registration_id: str,
    start_date: str,
    end_date: str
):
    registration_id = registration_id.strip()
    db_manager = make_db_manager(connection)
    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
    df_alarms_chunk_generator = telemetry_getter.get_flightswithalarms_by_marca_datetime_interval(
        marca=registration_id,
        start_datetime=start_date,
        end_datetime=end_date
    )
    if df_alarms_chunk_generator.dropna(how='all').empty:
        return []
    return [int(df_alarms_chunk_generator['numberoflights'][0])]


def get_top_flightswithalarms_by_registration_id(
    connection: ConnectionParamsHandler,
    registration_id: str,
    top: str,
    start_date: str,
    end_date: str
):
    registration_id = registration_id.strip()
    db_manager = make_db_manager(connection)
    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
    df_alarms_chunk_generator = telemetry_getter.get_top_flightswithalarms_by_marca_datetime_interval(
        marca=registration_id,
        top=top,
        start_datetime=start_date,
        end_datetime=end_date
    )
    if df_alarms_chunk_generator.dropna(how='all').empty:
        return []
    df_alarms_chunk_generator = df_alarms_chunk_generator.dropna(axis=1, how='all')
    return df_alarms_chunk_generator.to_dict(orient='records')


def get_flight_alarms_by_flight_id(connection: ConnectionParamsHandler, flight_id: int):
    db_manager = make_db_manager(connection)
    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
    df_chunk_generator = telemetry_getter.get_alarms_by_flight(id_volo=flight_id)
    if df_chunk_generator.dropna(how='all').empty:
        return []
    df_chunk_generator['total'] = df_chunk_generator.drop(['registration'], axis=1).sum(axis=1)
    df_chunk_generator = df_chunk_generator.dropna(axis=1, how='all')
    return df_chunk_generator.to_dict(orient='records')


def get_top_flight_alarms_by_flight_id(connection: ConnectionParamsHandler, flight_id: int, top: int):
    db_manager = make_db_manager(connection)
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
    df_chunk_generator = telemetry_getter.get_alarms_by_marca_datetime_interval(
        marca=flight.registration_id,
        start_datetime=flight.stick_on,
        end_datetime=flight.stick_off,
    )
    if df_chunk_generator.dropna(how='all').empty:
        return []
    df_alarms = df_chunk_generator.drop(['registration'], axis=1)
    df_top_alarms = df_alarms.iloc[0].sort_values(ascending=False, na_position='last')[:int(top)]
    df_result = df_top_alarms.to_dict()
    df_result['total'] = int(np.sum(df_top_alarms))
    df_result['registration'] = flight.registration_id
    return [df_result]


def get_all_recent_alarms_telemetry_pre(connection: ConnectionParamsHandler, start_date: str, end_date: str):
    db_manager = make_db_manager(connection)
    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)
    registration_getter = AirplaneInfoDBAccess(manager=db_manager)

    df_chunk_generator = registration_getter.get_all_airplane_with_flights_info()
    registration_ids = df_chunk_generator['marche'].tolist()

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
    telemetry_alarms_samples = telemetry_mapper.generate_telemetry_alarms(has_alarms=True)
    return [tel.as_dict() for tel in telemetry_alarms_samples]


def get_all_recent_alarms_telemetry_by_id_pre(
    connection: ConnectionParamsHandler,
    start_date: str,
    end_date: str,
    registration_ids: list[str],
):
    db_manager = make_db_manager(connection)
    telemetry_getter = TelemetryMQTTDatabaseAccess(manager=db_manager)

    if len(registration_ids) > 1:
        list_dfs = []
        for reg_id in registration_ids:
            df = telemetry_getter.get_telemetry_alarms_by_marca_datetime_interval(
                marca=reg_id.strip(), start_datetime=start_date, end_datetime=end_date
            )
            list_dfs.append(df)
        df_chunk_generator = pd.concat(list_dfs, ignore_index=True)
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
    telemetry_alarms_samples = telemetry_mapper.generate_telemetry_alarms(has_alarms=True)
    return list(map(lambda telemetry: telemetry.as_dict(), telemetry_alarms_samples))
