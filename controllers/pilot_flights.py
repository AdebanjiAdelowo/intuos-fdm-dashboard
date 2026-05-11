import datetime
import pandas as pd

from db_connection_params_handler import ConnectionParamsHandler
from db_factory import make_db_manager
from db_handlers.ibm_db2.pilot_flight_db_access import PilotFlightDBAccess


def get_all_pilot_flights(connection: ConnectionParamsHandler, pilot_id: str) -> list:
    pilot_id = pilot_id.strip()
    db_manager = make_db_manager(connection)
    flight_getter = PilotFlightDBAccess(manager=db_manager)
    df_chunk_generator = flight_getter.get_flights_by_pilot(pilot_id=pilot_id)
    if df_chunk_generator.dropna(how='all').empty:
        return []
    df_chunk_generator.rename(columns={'data_ora_decollo': 'stick_on', 'data_ora_atterraggio': 'stick_off'}, inplace=True)

    def safe_format(x):
        if isinstance(x, (pd.Timestamp, datetime.datetime)):
            return x.strftime("%Y-%m-%d %H:%M:%S.%f")
        return x

    df_chunk_generator[['stick_on', 'stick_off']] = df_chunk_generator[['stick_on', 'stick_off']].applymap(safe_format)
    return df_chunk_generator.to_dict(orient='records')


def get_flights_by_pilot_id_and_date(
    connection: ConnectionParamsHandler,
    pilot_id: str,
    start_date: str,
    end_date: str,
) -> list:
    pilot_id = pilot_id.strip()
    db_manager = make_db_manager(connection)
    flight_getter = PilotFlightDBAccess(manager=db_manager)
    df_chunk_generator = flight_getter.get_flights_by_pilot_datetime_interval(
        pilot_id=pilot_id, start_date=start_date, end_date=end_date
    )
    if df_chunk_generator.dropna(how='all').empty:
        return []
    df_chunk_generator.rename(columns={'data_ora_decollo': 'stick_on', 'data_ora_atterraggio': 'stick_off'}, inplace=True)

    def safe_format(x):
        if isinstance(x, (pd.Timestamp, datetime.datetime)):
            return x.strftime("%Y-%m-%d %H:%M:%S.%f")
        return x

    df_chunk_generator[['stick_on', 'stick_off']] = df_chunk_generator[['stick_on', 'stick_off']].applymap(safe_format)
    flights_length = df_chunk_generator.shape[0]
    return [{'flights_length': flights_length}]


def get_total_flewhourmin_by_pilot_id_and_date(
    connection: ConnectionParamsHandler,
    pilot_id: str,
    start_date: str,
    end_date: str,
) -> list:
    pilot_id = pilot_id.strip()
    db_manager = make_db_manager(connection)
    flight_getter = PilotFlightDBAccess(manager=db_manager)
    df_chunk_generator = flight_getter.get_flewhourmin_by_pilot_datetime_interval(
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
    db_manager = make_db_manager(connection)
    flight_getter = PilotFlightDBAccess(manager=db_manager)

    if len(pilot_ids) > 1:
        df_chunk_generator = flight_getter.get_flights_by_pilots_datetime_interval(
            marcas=pilot_ids, start_date=start_date, end_date=end_date
        )
    else:
        df_chunk_generator = flight_getter.get_flights_by_pilot_datetime_interval(
            marca=pilot_ids[0], start_date=start_date, end_date=end_date
        )

    if df_chunk_generator.dropna(how='all').empty:
        return []
    df_chunk_generator.rename(columns={'data_ora_decollo': 'stick_on', 'data_ora_atterraggio': 'stick_off'}, inplace=True)
    df_chunk_generator[['stick_on', 'stick_off']] = df_chunk_generator[['stick_on', 'stick_off']].map(lambda x: x.strftime("%Y-%m-%d %H:%M:%S.%f"))
    return df_chunk_generator.to_dict(orient='records')
