import numpy as np
from db_connection_params_handler import ConnectionParamsHandler
from db_handlers.ibm_db2.MQTT_db_access import PilotTelemetryMQTTDatabaseAccess
from db_factory import make_db_manager
from logic.position_assigner_instance import position_assigner
from mappers.telemetry_mapper import FormattedTelemetryMapper


def get_flight_telemetry_by_pilots_date_range(
    connection: ConnectionParamsHandler,
    pilot_ids: list[str],
    start_date: str,
    end_date: str,
) -> list[dict]:
    db_manager = make_db_manager(connection)
    telemetry_getter = PilotTelemetryMQTTDatabaseAccess(manager=db_manager)

    if len(pilot_ids) > 1:
        pilot_ids = [pilot_id.strip() for pilot_id in pilot_ids]
        df_chunk_generator = telemetry_getter.get_telemetry_by_pilots_datetime_interval(
            pilots=pilot_ids, start_datetime=start_date, end_datetime=end_date
        )
    else:
        df_chunk_generator = telemetry_getter.get_telemetry_by_pilot_datetime_interval(
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


def get_alarms_by_pilot_id(connection: ConnectionParamsHandler, pilot_id: str):
    pilot_id = pilot_id.strip()
    db_manager = make_db_manager(connection)
    telemetry_getter = PilotTelemetryMQTTDatabaseAccess(manager=db_manager)
    df_alarms_chunk_generator = telemetry_getter.get_alarms_by_pilot(pilot=pilot_id)
    if df_alarms_chunk_generator.dropna(how='all').empty:
        return []
    df_alarms_chunk_generator = df_alarms_chunk_generator.dropna(axis=1, how='all')
    return df_alarms_chunk_generator.to_dict(orient='records')


def get_all_recent_alarms_by_pilot_id(
    connection: ConnectionParamsHandler,
    pilot_id: str,
    start_date: str,
    end_date: str
):
    pilot_id = pilot_id.strip()
    db_manager = make_db_manager(connection)
    telemetry_getter = PilotTelemetryMQTTDatabaseAccess(manager=db_manager)
    df_alarms_chunk_generator = telemetry_getter.get_alarms_by_pilot_datetime_interval(
        pilot=pilot_id,
        start_datetime=start_date,
        end_datetime=end_date
    )
    if df_alarms_chunk_generator.dropna(how='all').empty:
        return []
    df_alarms_chunk_generator["total"] = df_alarms_chunk_generator.drop(["registration"], axis=1).sum(axis=1)
    df_alarms_chunk_generator = df_alarms_chunk_generator.dropna(axis=1, how='all')
    return df_alarms_chunk_generator.to_dict(orient='records')


def get_all_top_recent_alarms_by_pilot_id(
    connection: ConnectionParamsHandler,
    pilot_id: str,
    top: str,
    start_date: str,
    end_date: str
):
    pilot_id = pilot_id.strip()
    db_manager = make_db_manager(connection)
    telemetry_getter = PilotTelemetryMQTTDatabaseAccess(manager=db_manager)
    df_alarms_chunk_generator = telemetry_getter.get_alarms_by_pilot_datetime_interval(
        pilot=pilot_id,
        start_datetime=start_date,
        end_datetime=end_date
    )
    if df_alarms_chunk_generator.dropna(how='all').empty:
        return []
    df_alarms = df_alarms_chunk_generator.drop(['registration'], axis=1)
    df_top_alarms = df_alarms.iloc[0].sort_values(ascending=False, na_position='last')[:int(top)]
    df_result = df_top_alarms.to_dict()
    df_result['total'] = int(np.sum(df_top_alarms))
    df_result['pilot'] = pilot_id
    return [df_result]


def get_flightswithalarms_by_pilot_id(
    connection: ConnectionParamsHandler,
    pilot_id: str,
    start_date: str,
    end_date: str
):
    pilot_id = pilot_id.strip()
    db_manager = make_db_manager(connection)
    telemetry_getter = PilotTelemetryMQTTDatabaseAccess(manager=db_manager)
    df_alarms_chunk_generator = telemetry_getter.get_flightswithalarms_by_pilot_datetime_interval(
        pilot=pilot_id,
        start_datetime=start_date,
        end_datetime=end_date
    )
    if df_alarms_chunk_generator.dropna(how='all').empty:
        return []
    return [int(df_alarms_chunk_generator['numberoflights'][0])]


def get_top_flightswithalarms_by_pilot_id(
    connection: ConnectionParamsHandler,
    pilot_id: str,
    top: str,
    start_date: str,
    end_date: str
):
    pilot_id = pilot_id.strip()
    db_manager = make_db_manager(connection)
    telemetry_getter = PilotTelemetryMQTTDatabaseAccess(manager=db_manager)
    df_alarms_chunk_generator = telemetry_getter.get_top_flightswithalarms_by_pilot_datetime_interval(
        pilot=pilot_id,
        top=top,
        start_datetime=start_date,
        end_datetime=end_date
    )
    if df_alarms_chunk_generator.dropna(how='all').empty:
        return []
    df_alarms_chunk_generator = df_alarms_chunk_generator.dropna(axis=1, how='all')
    return df_alarms_chunk_generator.to_dict(orient='records')
