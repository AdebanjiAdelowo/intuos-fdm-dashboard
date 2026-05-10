# import cProfile
import asyncio
from fastapi import FastAPI, Request, Depends, Query
# from functools import lru_cache
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from controllers.login import do_login, retrieve_connection_params
from controllers.statistics import get_all_recent_alarms, get_all_recent_alarms_pre
from controllers.registration import (
    get_all_registrations, 
    get_all_registrations_count, 
    get_all_registrations_with_flights,
    get_all_registrations_with_flights_count
)

from controllers.pilots import (
    get_all_pilots, 
    get_paginated_pilots,
    search_pilots,
    get_all_pilots_count, 
    get_all_pilots_with_flights,
    get_all_pilots_with_flights_count
)

from controllers.telemetry import (
    get_flight_time_duration,
    get_alarms_by_registration_id,
    get_all_recent_alarms_telemetry,
    get_all_recent_alarms_telemetry_sync,
    get_all_recent_alarms_telemetry_pre,
    get_all_recent_alarms_telemetry_by_id_sync,
    get_all_recent_alarms_telemetry_by_id_pre,
    get_flight_alarms_by_flight_id,
    get_top_flight_alarms_by_flight_id,
    get_flight_telemetry_by_date_range_async,
    get_flight_telemetry_by_date_range_pre,
    get_flight_telemetry_by_date_range_sync,
    get_flight_telemetry_with_alarms_and_labels,
    get_all_recent_alarms_by_registration_id,
    get_all_top_recent_alarms_by_registration_id,
    get_flightswithalarms_by_registration_id,
    get_top_flightswithalarms_by_registration_id
)

from controllers.pilot_telemetry import (
    get_alarms_by_pilot_id,
    get_flight_telemetry_by_pilots_date_range,
    get_all_recent_alarms_by_pilot_id,
    get_all_top_recent_alarms_by_pilot_id,
    get_flightswithalarms_by_pilot_id,
    get_top_flightswithalarms_by_pilot_id
)
from controllers.flights import (
    get_all_flights,
    get_flights_by_registration_id_and_date,
    get_flights_by_registration_ids_and_date,
    get_all_registration_flights,
    get_total_flewhourmin_by_registration_id_and_date
)

from controllers.pilot_flights import (
    get_all_pilot_flights,
    get_flights_by_pilot_id_and_date,
    get_flights_by_pilot_ids_and_date, 
    get_total_flewhourmin_by_pilot_id_and_date
)
from db_connection_params_handler import ConnectionParamsHandler

app = FastAPI()

connection_filename = "config.yml"

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


def get_connection():
    return ConnectionParamsHandler(connection_filename=connection_filename)


@app.get("/luciano")
def read_root():
    """
    A simple endpoint that returns a JSON with a "Brau" key and the value "Lucià".

    Returns:
        JSONResponse: A JSON response with a status code of 200 and a dictionary containing the "Brau" key
    """
    return {"Brau": "Lucià"}


@app.post("/login")
async def login(request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Logs a user in and returns a JSON Web Token to be used in other API calls.

    Request body:
        email (str): The user's email
        password (str): The user's password

    Returns:
        JSONResponse: A JSON response with a status code of 200 and a dictionary containing the user and a token to be used in other API calls or a status code of 401 if the credentials are invalid
    """
    data = await request.json()
    email = data.get("email")
    password = data.get("password")
    user, token = do_login(connection=connection,email=email,password=password,)
    if (user is None) or (token is None):
        return JSONResponse(status_code=401, content={"message": "Invalid credentials"})
    return JSONResponse(
        status_code=200, content={"data": {"user": user, "token": token}}
    )


@app.get("/flights")
async def get_flights(request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all flights.

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all flights or a status code of 204 if no flights are found.
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    flights = await asyncio.to_thread(get_all_flights, connection) 
    if flights:
        return JSONResponse(status_code=200, content={"data": flights})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})


@app.get("/flight/{id}/time_duration")
async def get_flight_timeduration(id: int, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns all the telemetry with alarms for the given flight id.

    Parameters:
        id (int): The id of the flight

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the telemetry with alarms for the given flight id or a status code of 400 if no telemetry is found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    flight_duration = await asyncio.to_thread(get_flight_time_duration, connection, id)
    if len(flight_duration) > 0:
        return JSONResponse(status_code=200, content={"data": flight_duration})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})
    
    
@app.get("/telemetry/flight/{id}")
async def get_flight_telemetry(id: int, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns all the telemetry with alarms for the given flight id.

    Parameters:
        id (int): The id of the flight

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the telemetry with alarms for the given flight id or a status code of 400 if no telemetry is found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    flight_telemetry = await asyncio.to_thread(get_flight_telemetry_with_alarms_and_labels, connection, id)
    if len(flight_telemetry) > 0:
        return JSONResponse(status_code=200, content={"data": flight_telemetry})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})


@app.get("/registrations_with_flights")
async def get_registrations_with_flights(request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all registrations.

    Returns:
        JSONResponse: A JSON response with a status code of 200 and a list of all registrations or a status code of 400 if no registrations are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    registrations = await asyncio.to_thread(get_all_registrations_with_flights, connection)
    # registrations = await get_all_registrations_with_flights(connection)
    if len(registrations) > 0:
        return JSONResponse(status_code=200, content={"data": registrations})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})

@app.get("/pilots_with_flights")
async def get_pilots_with_flights(request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all registrations.

    Returns:
        JSONResponse: A JSON response with a status code of 200 and a list of all registrations or a status code of 400 if no registrations are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    pilots = await asyncio.to_thread(get_all_pilots_with_flights, connection)
    if len(pilots) > 0:
        return JSONResponse(status_code=200, content={"data": pilots})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})  
          
@app.get("/all_registrations")
async def get_registrations(request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all registrations.

    Returns:
        JSONResponse: A JSON response with a status code of 200 and a list of all registrations or a status code of 400 if no registrations are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    registrations = await asyncio.to_thread(get_all_registrations, connection)
    # registrations = await get_all_registrations(connection)
    if len(registrations) > 0:
        return JSONResponse(status_code=200, content={"data": registrations})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})


@app.get("/all_pilots")
async def get_pilots(request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all registrations.

    Returns:
        JSONResponse: A JSON response with a status code of 200 and a list of all registrations or a status code of 400 if no registrations are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    pilots = await asyncio.to_thread(get_all_pilots, connection)
    if len(pilots) > 0:
        return JSONResponse(status_code=200, content={"data": pilots})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})
    
@app.get("/all_pilots_pg/{start_date}/{end_date}")
async def get_pilots_pg(
    start_date: str, 
    end_date: str,
    request: Request, 
    connection: ConnectionParamsHandler = Depends(get_connection),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    """
    Returns a paginated list of pilots.

    Parameters:
        request: The HTTP request
        connection: Database connection parameters
        page: Page number (starts at 1)
        page_size: Number of items per page (default 10, max 100)

    Returns:
        JSONResponse: A JSON response with paginated list of pilots
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    
    pilots, total_count = await asyncio.to_thread(
        get_paginated_pilots, 
        connection, 
        start_date,
        end_date,
        page, 
        page_size
    )
    
    if not pilots:
        if total_count == 0:
            return JSONResponse(status_code=204, content={"message": "no data"})
        else:
            # This might happen if the page number is beyond available data
            return JSONResponse(status_code=200, content={
                "data": [],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_count,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "has_next": False,
                    "has_prev": page > 1
                }
            })
    
    # Calculate pagination metadata
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
    total_pages = int(total_pages)
    total_count = int(total_count)
    return JSONResponse(
        status_code=200, 
        content={
            "data": pilots,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    )
    

@app.get("/all_pilots_search/{start_date}/{end_date}")
async def get_pilots_search(
    start_date: str, 
    end_date: str,
    request: Request, 
    connection: ConnectionParamsHandler = Depends(get_connection),
    search: str = Query(None, description="Search term for pilot name"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    """
    Returns a filtered and paginated list of pilots.

    Parameters:
        request: The HTTP request
        connection: Database connection parameters
        search: Optional search term to filter pilots by name
        page: Page number (starts at 1)
        page_size: Number of items per page (default 10, max 100)

    Returns:
        JSONResponse: A JSON response with filtered and paginated list of pilots
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    
    pilots, total_count = await asyncio.to_thread(
        search_pilots, 
        connection,
        start_date,
        end_date,
        search,
        page, 
        page_size
    )
    
    if not pilots:
        if total_count == 0:
            return JSONResponse(status_code=204, content={"message": "no data"})
        else:
            # This might happen if the page number is beyond available data
            return JSONResponse(status_code=200, content={
                "data": [],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_items": total_count,
                    "total_pages": (total_count + page_size - 1) // page_size,
                    "has_next": False,
                    "has_prev": page > 1
                },
                "search": search
            })
    
    # Calculate pagination metadata
    total_pages = (total_count + page_size - 1) // page_size  # Ceiling division

    total_pages = int(total_pages)
    total_count = int(total_count)
    
    return JSONResponse(
        status_code=200, 
        content={
            "data": pilots,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_count,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "search": search
        }
    )
    
    
@app.get("/all_registrations_count")
async def get_registrations_count(request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all registrations.

    Returns:
        JSONResponse: A JSON response with a status code of 200 and a list of all registrations or a status code of 400 if no registrations are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    
    try:
        registrations_count = await asyncio.to_thread(get_all_registrations_count, connection)
        return JSONResponse(status_code=200, content={"data": int(registrations_count)})
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    
@app.get("/all_pilots_count")
async def get_pilots_count(request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all pilots.

    Returns:
        JSONResponse: A JSON response with a status code of 200 and a list of all pilots or a status code of 400 if no registrations are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    
    try:
        pilots_count = await asyncio.to_thread(get_all_pilots_count, connection)
        return JSONResponse(status_code=200, content={"data": int(pilots_count)})
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    
@app.get("/registrations_with_flights_count")
async def get_registrations_with_flights_count(request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all registrations.

    Returns:
        JSONResponse: A JSON response with a status code of 200 and a list of all registrations or a status code of 400 if no registrations are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    
    try:
        registrations_count = await asyncio.to_thread(get_all_registrations_with_flights_count, connection)
        # registrations_count = await get_all_registrations_with_flights_count(connection)
        return JSONResponse(status_code=200, content={"data": int(registrations_count)})
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    
@app.get("/pilots_with_flights_count")
async def get_pilots_with_flights_count(request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all registrations.

    Returns:
        JSONResponse: A JSON response with a status code of 200 and a list of all registrations or a status code of 400 if no registrations are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    
    try:
        pilots_count = await asyncio.to_thread(get_all_pilots_with_flights_count, connection)
        return JSONResponse(status_code=200, content={"data": int(pilots_count)})
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})  
          
@app.get("/registrations/alarms/{start_date}/{end_date}")
async def get_alarms(start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns all the alarms in the given date range.

    Path Parameters:
        start_date: str - The start of the date range in ISO 8601 format
        end_date: str - The end of the date range in ISO 8601 format

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the alarms in the given date range or a status code of 400 if no alarms are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)}) 
    recent_alarms = await asyncio.to_thread(get_all_recent_alarms_pre, connection, start_date, end_date)
    # recent_alarms = await asyncio.to_thread(get_all_recent_alarms, connection, start_date, end_date)
    # recent_alarms = await get_all_recent_alarms(connection, start_date, end_date)

    if len(recent_alarms) > 0:
        return JSONResponse(status_code=200, content={"data": recent_alarms})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})
        
@app.get("/top_registrations/alarms/{top}/{start_date}/{end_date}")
async def get_top_registrations_by_alarms(top: str, start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns the top registrations by alarms in the given date range.

    Path Parameters:
        start_date: str - The start of the date range in ISO 8601 format
        end_date: str - The end of the date range in ISO 8601 format

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the alarms in the given date range or a status code of 400 if no alarms are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    recent_alarms = await asyncio.to_thread(get_all_recent_alarms_pre, connection, start_date, end_date)
    # recent_alarms = await get_all_recent_alarms(connection, start_date, end_date)

    if len(recent_alarms) > 0:
        return JSONResponse(status_code=200, content={"data": recent_alarms[:int(top)]})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})
    

@app.get("/registration/{registration_id}/flights")
async def get_flights_by_registration(registration_id: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns all the flights for the given registration id.

    Path Parameters:
        registration_id (str): The id of the registration

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the flights for the given registration id or a status code of 400 if no flights are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    flights = await asyncio.to_thread(get_all_registration_flights, connection, registration_id)
    if len(flights) > 0:
        return JSONResponse(status_code=200, content={"data": flights})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})

@app.get("/pilot/{pilot_id}/flights")
async def get_flights_by_pilot(pilot_id: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns all the flights for the given pilot id.

    Path Parameters:
        pilot_id (str): The id of the registration

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the flights for the given registration id or a status code of 400 if no flights are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    flights = await asyncio.to_thread(get_all_pilot_flights, connection, pilot_id) 
    if len(flights) > 0:
        return JSONResponse(status_code=200, content={"data": flights})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})
    
@app.get("/registration/{registration_id}/flights/{start_date}/{end_date}")
async def get_flights_by_registration_and_date(
    registration_id: str, start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)
):
    """
    Returns all the flights for the given registration id in the given date range.

    Path Parameters:
        registration_id (str): The id of the registration
        start_date (str): The start of the time range in ISO 8601 format
        end_date (str): The end of the time range in ISO 8601 format

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the flights for the given registration id in the given date range or a status code of 400 if no flights are found
    """
    try:    
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    flights = await asyncio.to_thread(get_flights_by_registration_id_and_date, 
                                        connection, 
                                        registration_id,
                                        start_date,
                                        end_date)
    if len(flights) > 0:
        return JSONResponse(status_code=200, content={"data": flights})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})

@app.get("/pilot/{pilot_id}/flights/{start_date}/{end_date}")
async def get_flights_by_pilot_and_date(
    pilot_id: str, start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)
):
    """
    Returns all the flights for the given pilot id in the given date range.

    Path Parameters:
        pilot_id (str): The id of the pilot
        start_date (str): The start of the time range in ISO 8601 format
        end_date (str): The end of the time range in ISO 8601 format

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the flights for the given registration id in the given date range or a status code of 400 if no flights are found
    """
    try:    
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    flights = await asyncio.to_thread(get_flights_by_pilot_id_and_date, 
                                        connection, 
                                        pilot_id,
                                        start_date,
                                        end_date)
    if len(flights) > 0:
        return JSONResponse(status_code=200, content={"data": flights})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})
    
@app.get("/flewhours/pilot/{pilot_id}/flights/{start_date}/{end_date}")
async def get_total_flewhourmins_by_pilot_and_date(
    pilot_id: str, start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)
):
    """
    Returns all the flights for the given registration id in the given date range.

    Path Parameters:
        pilot_id (str): The id of the registration
        start_date (str): The start of the time range in ISO 8601 format
        end_date (str): The end of the time range in ISO 8601 format

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the flights for the given registration id in the given date range or a status code of 400 if no flights are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})

    flewhoursmins = await asyncio.to_thread(get_total_flewhourmin_by_pilot_id_and_date,
                                            connection,
                                            pilot_id,
                                            start_date,
                                            end_date
                                            )
    if len(flewhoursmins) > 0:
        return JSONResponse(status_code=200, content={"data": flewhoursmins})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})

@app.get("/flewhours/registration/{registration_id}/flights/{start_date}/{end_date}")
async def get_total_flewhourmins_by_registration_and_date(
    registration_id: str, start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)
):
    """
    Returns all the flights for the given registration id in the given date range.

    Path Parameters:
        registration_id (str): The id of the registration
        start_date (str): The start of the time range in ISO 8601 format
        end_date (str): The end of the time range in ISO 8601 format

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the flights for the given registration id in the given date range or a status code of 400 if no flights are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})

    flewhoursmins = await asyncio.to_thread(get_total_flewhourmin_by_registration_id_and_date,
                                            connection,
                                            registration_id,
                                            start_date,
                                            end_date
                                            )
    if len(flewhoursmins) > 0:
        return JSONResponse(status_code=200, content={"data": flewhoursmins})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})

@app.post("/registration/flights/{start_date}/{end_date}")
async def get_flights_by_registration_and_date( 
    start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)
):
    """
    Returns a list of all flights for the given registration ids in the given time range.

    Path Parameters:
        start_date (str): The start of the time range in ISO 8601 format
        end_date (str): The end of the time range in ISO 8601 format

    Request body:
        registration_ids (list[str]): The list of registration ids to retrieve flights for.

    Returns:
        JSONResponse: A JSON response containing the list of flights. The status code is 200 if flights are found, 400 otherwise.
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})

    data = await request.json()
    registration_ids = data.get("registration_ids")
    
    if isinstance(registration_ids, list): 
        all_flights = await asyncio.to_thread(get_flights_by_registration_ids_and_date,
                                                connection,
                                                registration_ids,
                                                start_date,
                                                end_date
                                                )
    else:
        registration_ids = [registration_ids]
        all_flights = await asyncio.to_thread(get_flights_by_registration_ids_and_date,
                                                connection,
                                                registration_ids,
                                                start_date,
                                                end_date
                                                )
    if len(all_flights) > 0:
        return JSONResponse(status_code=200, content={"data": all_flights})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})

@app.post("/pilot/flights/{start_date}/{end_date}")
async def get_flights_by_pilots_and_date( 
    start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)
):
    """
    Returns a list of all flights for the given registration ids in the given time range.

    Path Parameters:
        start_date (str): The start of the time range in ISO 8601 format
        end_date (str): The end of the time range in ISO 8601 format

    Request body:
        pilot_ids (list[str]): The list of pilot ids to retrieve flights for.

    Returns:
        JSONResponse: A JSON response containing the list of flights. The status code is 200 if flights are found, 400 otherwise.
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})

    data = await request.json()
    pilot_ids = data.get("pilot_ids")
    
    if isinstance(pilot_ids, list): 
        all_flights = await asyncio.to_thread(get_flights_by_pilot_ids_and_date,
                                                connection,
                                                pilot_ids,
                                                start_date,
                                                end_date
                                                )
    else:
        pilot_ids = [pilot_ids]
        all_flights = await asyncio.to_thread(get_flights_by_pilot_ids_and_date,
                                                connection,
                                                pilot_ids,
                                                start_date,
                                                end_date
                                                )
    if len(all_flights) > 0:
        return JSONResponse(status_code=200, content={"data": all_flights})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})
    
    
@app.get("/registration/{registration_id}/telemetry/{start_date}/{end_date}")
async def get_flight_telemetry_by_registration(
    registration_id: str, start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)
):
    """
    Returns all the telemetry for the given registration id in the given time range.

    Parameters:
    - registration_id (str): The id of the registration
    - start_date (str): The start of the time range in ISO 8601 format
    - end_date (str): The end of the time range in ISO 8601 format

    Returns:
    - JSONResponse: A JSON response containing the telemetry. The status code is 200 if telemetry is found, 400 otherwise.
    """

    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    registration_ids = [registration_id]
    flight_telemetry = await asyncio.to_thread(get_flight_telemetry_by_date_range_pre,
                                                connection,
                                                registration_ids,
                                                start_date,
                                                end_date)
    if len(flight_telemetry) > 0:
        return JSONResponse(status_code=200, content={"data": flight_telemetry})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})

@app.get("/pilot/{pilot_id}/telemetry/{start_date}/{end_date}")
async def get_flight_telemetry_by_pilot(
    pilot_id: str, start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)
):
    """
    Returns all the telemetry for the given registration id in the given time range.

    Parameters:
    - pilot_id (str): The id of the registration
    - start_date (str): The start of the time range in ISO 8601 format
    - end_date (str): The end of the time range in ISO 8601 format

    Returns:
    - JSONResponse: A JSON response containing the telemetry. The status code is 200 if telemetry is found, 400 otherwise.
    """

    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    pilot_ids = [pilot_id]
    flight_telemetry = await asyncio.to_thread(get_flight_telemetry_by_pilots_date_range,
                                                connection,
                                                pilot_ids,
                                                start_date,
                                                end_date)
    if len(flight_telemetry) > 0:
        return JSONResponse(status_code=200, content={"data": flight_telemetry})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})

@app.post("/registration/telemetry/{start_date}/{end_date}")
async def get_flight_telemetry_by_registration(
    start_date: str, end_date: str, request: Request , connection: ConnectionParamsHandler = Depends(get_connection)
):
    """
    Returns a list of telemetry with alarms for the given registrations and time range.

    Path Parameters:
        start_date (str): The start of the time range in ISO 8601 format.
        end_date (str): The end of the time range in ISO 8601 format.

    Request Body:
        registration_ids (list[str]): The list of registrations to retrieve telemetry for.

    Returns:
        JSONResponse: A response containing the telemetry with alarms. The status code is 200 if telemetry is found, 400 otherwise.
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})

    data = await request.json()
    registration_ids: list[str] = data.get("registration_ids")
    
    if isinstance(registration_ids, list):
        all_telemetries = await asyncio.to_thread(get_flight_telemetry_by_date_range_pre,
                                                connection,
                                                registration_ids,
                                                start_date,
                                                end_date)
        
        # all_telemetries = await get_flight_telemetry_by_date_range(
        #                                 connection,
        #                                 registration_ids,
        #                                 start_date,
        #                                 end_date
        #                                 )
    else:
        registration_ids = [registration_ids]
        all_telemetries = await asyncio.to_thread(get_flight_telemetry_by_date_range_pre,
                                                connection,
                                                registration_ids,
                                                start_date,
                                                end_date)
        
        # all_telemetries = await get_flight_telemetry_by_date_range(
        #                                     connection,
        #                                     registration_ids,
        #                                     start_date,
        #                                     end_date
        #                                     )
    if len(all_telemetries) > 0:
        return JSONResponse(status_code=200, content={"data": all_telemetries})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})
    

@app.post("/pilot/telemetry/{start_date}/{end_date}")
async def get_flight_telemetry_by_pilots(
    start_date: str, end_date: str, request: Request , connection: ConnectionParamsHandler = Depends(get_connection)
):
    """
    Returns a list of telemetry with alarms for the given registrations and time range.

    Path Parameters:
        start_date (str): The start of the time range in ISO 8601 format.
        end_date (str): The end of the time range in ISO 8601 format.

    Request Body:
        pilot_ids (list[str]): The list of registrations to retrieve telemetry for.

    Returns:
        JSONResponse: A response containing the telemetry with alarms. The status code is 200 if telemetry is found, 400 otherwise.
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})

    data = await request.json()
    pilot_ids: list[str] = data.get("registration_ids")
    
    if isinstance(pilot_ids, list):
        all_telemetries = await asyncio.to_thread(get_flight_telemetry_by_pilots_date_range,
                                                    connection,
                                                    pilot_ids,
                                                    start_date,
                                                    end_date)
    else:
        pilot_ids = [pilot_ids]
        all_telemetries = await asyncio.to_thread(get_flight_telemetry_by_pilots_date_range,
                                                connection,
                                                pilot_ids,
                                                start_date,
                                                end_date
                                                )
    if len(all_telemetries) > 0:
        return JSONResponse(status_code=200, content={"data": all_telemetries})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})


@app.get("/registration/{registration_id}/alarms")
async def get_alarms_by_registration(registration_id: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all alarms for the given registration id.

    Path Parameters:
        registration_id: str - The id of the registration

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the alarms for the given registration id or a status code of 400 if no alarms are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    alarms = await asyncio.to_thread(get_alarms_by_registration_id, connection, registration_id)
    if len(alarms) > 0:
        return JSONResponse(status_code=200, content={"data": alarms})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})
    
    
@app.get("/pilot/{pilot_id}/alarms")
async def get_alarms_by_pilot(pilot_id: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all alarms for the given registration id.

    Path Parameters:
        registration_id: str - The id of the registration

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the alarms for the given registration id or a status code of 400 if no alarms are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    alarms = await asyncio.to_thread(get_alarms_by_pilot_id, connection, pilot_id)
    if len(alarms) > 0:
        return JSONResponse(status_code=200, content={"data": alarms})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})
   
    
@app.get("/registration/{registration_id}/alarms/{start_date}/{end_date}")
async def get_all_recent_alarms_by_registration(registration_id: str, start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all alarms for the given registration id.

    Path Parameters:
        registration_id: str - The id of the registration

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the alarms for the given registration id or a status code of 400 if no alarms are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    
    alarms = await asyncio.to_thread(get_all_recent_alarms_by_registration_id,
                                    connection,
                                    registration_id,
                                    start_date,
                                    end_date)
    if len(alarms) > 0:
        return JSONResponse(status_code=200, content={"data": alarms})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})
    
    

@app.get("/pilot/{pilot_id}/alarms/{start_date}/{end_date}")
async def get_all_recent_alarms_by_registration(pilot_id: str, start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all alarms for the given pilot id.

    Path Parameters:
        pilot_id: str - The id of the registration

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the alarms for the given pilot id or a status code of 400 if no alarms are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    
    alarms = await asyncio.to_thread(get_all_recent_alarms_by_pilot_id,
                                    connection,
                                    pilot_id,
                                    start_date,
                                    end_date)
    if len(alarms) > 0:
        return JSONResponse(status_code=200, content={"data": alarms})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})


@app.get("/registration/{registration_id}/{top}/alarms/{start_date}/{end_date}")
async def get_top_recent_alarms_by_registration(registration_id: str, top: str, start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all alarms for the given registration id.

    Path Parameters:
        registration_id: str - The id of the registration

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the alarms for the given registration id or a status code of 400 if no alarms are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})

    top_alarms = await asyncio.to_thread(get_all_top_recent_alarms_by_registration_id,
                                        connection,
                                        registration_id,
                                        top,
                                        start_date,
                                        end_date)
    if len(top_alarms) > 0:
        return JSONResponse(status_code=200, content={"data": top_alarms})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})

@app.get("/pilot/{pilot_id}/{top}/alarms/{start_date}/{end_date}")
async def get_top_recent_alarms_by_pilot(pilot_id: str, top: str, start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all alarms for the given pilot id.

    Path Parameters:
        pilot_id: str - The id of the pilot

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the alarms for the given pilot id or a status code of 400 if no alarms are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})

    top_alarms = await asyncio.to_thread(get_all_top_recent_alarms_by_pilot_id,
                                        connection,
                                        pilot_id,
                                        top,
                                        start_date,
                                        end_date)
    if len(top_alarms) > 0:
        return JSONResponse(status_code=200, content={"data": top_alarms})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})    
    
@app.get("/registration/{registration_id}/flightswithalarms/{start_date}/{end_date}")
async def get_flight_with_alarms_by_registration(registration_id: str, start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all alarms for the given registration id.

    Path Parameters:
        registration_id: str - The id of the registration

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the alarms for the given registration id or a status code of 400 if no alarms are found
    """

    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    flights_with_alarms_count = await asyncio.to_thread(get_flightswithalarms_by_registration_id,
                                                        connection,
                                                        registration_id,
                                                        start_date,
                                                        end_date)
    if len(flights_with_alarms_count) > 0:
        return JSONResponse(status_code=200, content={"data": flights_with_alarms_count[0]})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})
    
@app.get("/pilot/{pilot_id}/flightswithalarms/{start_date}/{end_date}")
async def get_flight_with_alarms_by_pilot(pilot_id: str, start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all alarms for the given pilot id.

    Path Parameters:
        pilot_id: str - The id of the pilot

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the alarms for the given pilot id or a status code of 400 if no alarms are found
    """

    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    flights_with_alarms_count = await asyncio.to_thread(get_flightswithalarms_by_pilot_id,
                                                        connection,
                                                        pilot_id,
                                                        start_date,
                                                        end_date)
    if len(flights_with_alarms_count) > 0:
        return JSONResponse(status_code=200, content={"data": flights_with_alarms_count[0]})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})
    
@app.get("/registration/{registration_id}/top_flightswithalarms/{top}/{start_date}/{end_date}")
async def get_top_flight_with_alarms_by_registration(registration_id: str, top: str, start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all alarms for the given registration id.

    Path Parameters:
        registration_id: str - The id of the registration

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the alarms for the given registration id or a status code of 400 if no alarms are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    flights_with_alarms = await asyncio.to_thread(get_top_flightswithalarms_by_registration_id,
                                                connection,
                                                registration_id,
                                                top,
                                                start_date,
                                                end_date)
    if len(flights_with_alarms) > 0:
        return JSONResponse(status_code=200, content={"data": flights_with_alarms})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})

@app.get("/pilot/{pilot_id}/top_flightswithalarms/{top}/{start_date}/{end_date}")
async def get_top_flight_with_alarms_by_pilot(pilot_id: str, top: str, start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all alarms for the given pilot id.

    Path Parameters:
        pilot_id: str - The id of the registration

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the alarms for the given pilot id or a status code of 400 if no alarms are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    flights_with_alarms = await asyncio.to_thread(get_top_flightswithalarms_by_pilot_id,
                                                        connection,
                                                        pilot_id,
                                                        top,
                                                        start_date,
                                                        end_date)
    if len(flights_with_alarms) > 0:
        return JSONResponse(status_code=200, content={"data": flights_with_alarms})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})
    
@app.get("/alarms/flight/{id}")
async def get_flight_alarms_by_flight(id: int, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns all the alarms for the given flight id.

    Path Parameters:
        id: int - The id of the flight

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the alarms for the given flight id or a status code of 400 if no alarms are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    alarms = await asyncio.to_thread(get_flight_alarms_by_flight_id, connection, id)
    if len(alarms) > 0:
        return JSONResponse(status_code=200, content={"data": alarms})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})
    
    
@app.get("/alarms/flight/{id}/{top}")
async def get_top_flight_alarms_by_flight(id: int, top:int, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns all the alarms for the given flight id.

    Path Parameters:
        id: int - The id of the flight

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the alarms for the given flight id or a status code of 400 if no alarms are found
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    top_alarms = await asyncio.to_thread(get_top_flight_alarms_by_flight_id, connection, id, top)
    if len(top_alarms) > 0:
        return JSONResponse(status_code=200, content={"data": top_alarms})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})

@app.get("/registrations/alarms/telemetry/{start_date}/{end_date}")
async def get_alarms_by_telemetry(start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of all the recent alarms in the given date range.

    Path Parameters:
        start_date: str - The start date of the range in the format %Y-%m-%d %H:%M:%S
        end_date: str - The end date of the range in the format %Y-%m-%d %H:%M:%S

    Returns:
        JSONResponse - A JSON response with a status code of 200 and a list of all the recent alarms in the given date range
    """
    try:
        connection = await asyncio.to_thread(retrieve_connection_params, request, connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})
    
    # alarm_telemetry = await asyncio.to_thread(get_all_recent_alarms_telemetry_sync, connection, start_date, end_date)
    alarm_telemetry = await asyncio.to_thread(get_all_recent_alarms_telemetry_pre, connection, start_date, end_date)

    # alarm_telemetry = await get_all_recent_alarms_telemetry(connection, start_date, end_date)

    if len(alarm_telemetry) > 0:
        return JSONResponse(status_code=200, content={"data": alarm_telemetry})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})


@app.post("/registration/alarms/telemetry/{start_date}/{end_date}")
async def get_alarms_by_telemetry(start_date: str, end_date: str, request: Request, connection: ConnectionParamsHandler = Depends(get_connection)):
    """
    Returns a list of telemetry with alarms for the given registrations and time range.

    Parameters:
    - start_date (str): The start of the time range in ISO 8601 format.
    - end_date (str): The end of the time range in ISO 8601 format.
    - request (Request): The request object, used to retrieve the connection parameters.

    Request body:
    - registration_ids (list[str]): The list of registrations to retrieve telemetry for.

    Returns:
    - JSONResponse: A response containing the telemetry with alarms. The status code is 200 if telemetry is found, 400 otherwise.
    """
    try:
        connection = retrieve_connection_params(request=request, connection=connection)
    except Exception as e:
        return JSONResponse(status_code=401, content={"message": str(e)})

    data = await request.json()
    registration_ids: list[str] = data.get("registration_ids")
    
    if isinstance(registration_ids, list):
        alarm_telemetries = await asyncio.to_thread(get_all_recent_alarms_telemetry_by_id_pre,
                                                    connection,
                                                    start_date,
                                                    end_date,
                                                    registration_ids)
        
        # alarm_telemetries = await get_all_recent_alarms_telemetry_by_id(
        #                                             connection,
        #                                             start_date,
        #                                             end_date,
        #                                             registration_ids
        #                                             )
    else:
        registration_ids = [registration_ids]
        alarm_telemetries = await asyncio.to_thread(get_all_recent_alarms_telemetry_by_id_pre,
                                                    connection,
                                                    start_date,
                                                    end_date, 
                                                    registration_ids)
        
        # alarm_telemetries = await get_all_recent_alarms_telemetry_by_id(
        #                                             connection,
        #                                             start_date,
        #                                             end_date,
        #                                             registration_ids
        #                                             )
            
    if len(alarm_telemetries) > 0:
        return JSONResponse(status_code=200, content={"data": alarm_telemetries})
    else:
        return JSONResponse(status_code=204, content={"message": "no data"})


def main():
    """
    Starts the FastAPI app in a uvicorn web server.

    Host and port are hardcoded for now.
    """
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5001)
    # uvicorn.run(app, host="localhost", port=5002)


if __name__ == "__main__":
    main()
