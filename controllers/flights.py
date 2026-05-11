from db_connection_params_handler import ConnectionParamsHandler
from db_factory import make_db_manager
from db_handlers.ibm_db2.flight_db_access import FlightDBAccess
from mappers.flight_mapper import FlightMapper
from datamodels import Flight


def get_all_flights(connection: ConnectionParamsHandler) -> list:
    db_manager = make_db_manager(connection)
    flight_getter = FlightDBAccess(manager=db_manager)
    df_chunk_generator = flight_getter.get_all_flights()
    if df_chunk_generator.dropna(how='all').empty:
        return []
    flight_mapper = FlightMapper(df_chunk_generator=df_chunk_generator)
    flights = flight_mapper.generate_converted_flights()
    return flights.apply(Flight.as_dict).tolist()


def get_all_registration_flights(connection: ConnectionParamsHandler, registration_id: str) -> list:
    registration_id = registration_id.strip()
    db_manager = make_db_manager(connection)
    flight_getter = FlightDBAccess(manager=db_manager)
    df_chunk_generator = flight_getter.get_flights_by_marche(marca=registration_id)
    if df_chunk_generator.dropna(how='all').empty:
        return []
    df_chunk_generator.rename(columns={'data_ora_decollo': 'stick_on', 'data_ora_atterraggio': 'stick_off'}, inplace=True)
    df_chunk_generator[['stick_on', 'stick_off']] = df_chunk_generator[['stick_on', 'stick_off']].map(lambda x: x.strftime("%Y-%m-%d %H:%M:%S.%f"))
    return df_chunk_generator.to_dict(orient='records')


def get_flights_by_registration_id_and_date(
    connection: ConnectionParamsHandler,
    registration_id: str,
    start_date: str,
    end_date: str,
) -> list:
    registration_id = registration_id.strip()
    db_manager = make_db_manager(connection)
    flight_getter = FlightDBAccess(manager=db_manager)
    df_chunk_generator = flight_getter.get_flights_by_marche_datetime_interval(
        marca=registration_id, start_date=start_date, end_date=end_date
    )
    if df_chunk_generator.dropna(how='all').empty:
        return []
    df_chunk_generator.rename(columns={'data_ora_decollo': 'stick_on', 'data_ora_atterraggio': 'stick_off'}, inplace=True)
    df_chunk_generator[['stick_on', 'stick_off']] = df_chunk_generator[['stick_on', 'stick_off']].map(lambda x: x.strftime("%Y-%m-%d %H:%M:%S.%f"))
    flights_length = df_chunk_generator.shape[0]
    result = {
        "flights": df_chunk_generator.to_dict(orient='records'),
        "flights_length": flights_length,
    }
    return [result]


def get_total_flewhourmin_by_registration_id_and_date(
    connection: ConnectionParamsHandler,
    registration_id: str,
    start_date: str,
    end_date: str,
) -> list:
    registration_id = registration_id.strip()
    db_manager = make_db_manager(connection)
    flight_getter = FlightDBAccess(manager=db_manager)
    df_chunk_generator = flight_getter.get_flewhourmin_by_marche_datetime_interval(
        marca=registration_id, start_date=start_date, end_date=end_date
    )
    if df_chunk_generator.dropna(how='all').empty:
        return []
    return df_chunk_generator.to_dict(orient='records')


def get_flights_by_registration_ids_and_date(
    connection: ConnectionParamsHandler,
    registration_ids: list[str],
    start_date: str,
    end_date: str,
) -> list:
    db_manager = make_db_manager(connection)
    flight_getter = FlightDBAccess(manager=db_manager)

    if len(registration_ids) > 1:
        df_chunk_generator = flight_getter.get_flights_by_marches_datetime_interval(
            marcas=registration_ids, start_date=start_date, end_date=end_date
        )
    else:
        df_chunk_generator = flight_getter.get_flights_by_marche_datetime_interval(
            marca=registration_ids[0], start_date=start_date, end_date=end_date
        )

    if df_chunk_generator.dropna(how='all').empty:
        return []
    df_chunk_generator.rename(columns={'data_ora_decollo': 'stick_on', 'data_ora_atterraggio': 'stick_off'}, inplace=True)
    df_chunk_generator[['stick_on', 'stick_off']] = df_chunk_generator[['stick_on', 'stick_off']].map(lambda x: x.strftime("%Y-%m-%d %H:%M:%S.%f"))
    return df_chunk_generator.to_dict(orient='records')
