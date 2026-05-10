from datetime import datetime
import pandas as pd

from converters.flight_separator import FlightSeparator
from converters.format_mqtt_dataset import format_mqtt_message_dataset
from datamodels import AirplaneDatasheet, Alarm, Flight, TelemetrySample


def airplane_datasheets_mapper(df: pd.DataFrame) -> dict[str:AirplaneDatasheet]:
    
    # airplane_datasheets = df.copy()[["marche", "country", "typedesignator"]].rename(
    #     columns={
    #         "marche": "registration",
    #         "country": "country",
    #         "typedesignator": "typedesignator",
    #     }
    # )
    
    # airplane_datasheets = df[["marche", "country", "typedesignator"]].copy().rename(
    #     columns={
    #         "marche": "registration",
    #         "country": "country",
    #         "typedesignator": "typedesignator",
    #     }
    # )
    # return {
    #     row["registration"]: AirplaneDatasheet(
    #         registration_name=row["registration"],
    #         country=row["country"],
    #         typedesignator=row["typedesignator"],
    #     )
    #     for index, row in airplane_datasheets.iterrows()
    # }

    airplane_datasheets = df[["marche", "country", "typedesignator"]].rename(
        columns={
            "marche": "registration",
            "country": "country",
            "typedesignator": "typedesignator",
        }, inplace=True
    )
    return {
        row.registration: AirplaneDatasheet(
            registration_name=row.registration,
            country=row.country,
            typedesignator=row.typedesignator,
        )
        for row in airplane_datasheets.itertuples(index=False)
    }


def alarms_mapper(df: pd.DataFrame) -> list[Alarm]:
    """
    Maps a pandas DataFrame to a list of Alarm objects.

    This function takes a pandas DataFrame as its argument and returns a list of
    Alarm objects. The DataFrame should contain the columns marche, vcc_min,
    vcc_max, icc_min, icc_max, tint_min, tint_max, gtot_min, gtot_max, ias_max,
    vsi_max, pitch_max, roll_max, height_min, altitude_max. The values in
    these columns are used to fill the corresponding attributes in the returned
    Alarm objects.

    Parameters
    ----------
    df : pandas.DataFrame
        A pandas DataFrame containing the columns marche, vcc_min, vcc_max,
        icc_min, icc_max, tint_min, tint_max, gtot_min, gtot_max, ias_max,
        vsi_max, pitch_max, roll_max, height_min, altitude_max.

    Returns
    -------
    list[Alarm]
        A list of Alarm objects containing the values from the DataFrame.
    """
    
    # alarms = df.copy().rename(
    #     columns={
    #         "marche": "registration",
    #         "vcc_min": "vcc_min",
    #         "vcc_max": "vcc_max",
    #         "icc_min": "icc_min",
    #         "icc_max": "icc_max",
    #         "tint_min": "temperature_box_min",
    #         "tint_max": "temperature_box_max",
    #         "gtot_min": "g_tot_min",
    #         "gtot_max": "g_tot_max",
    #         "ias_max": "ground_speed_max",
    #         "vsi_max": "vertical_speed_max",
    #         "pitch_max": "pitch_max",
    #         "roll_max": "roll_max",
    #         "height_min": "height_min",
    #         "altitude_max": "altitude_max",
    #     }
    # )
    # return [
    #     Alarm(
    #         vcc_min=row["vcc_min"],
    #         vcc_max=row["vcc_max"],
    #         icc_min=row["icc_min"],
    #         icc_max=row["icc_max"],
    #         temperature_box_min=row["temperature_box_min"],
    #         temperature_box_max=row["temperature_box_max"],
    #         g_tot_min=row["g_tot_min"],
    #         g_tot_max=row["g_tot_max"],
    #         ground_speed_max=row["ground_speed_max"],
    #         vertical_speed_max=row["vertical_speed_max"],
    #         pitch_max=row["pitch_max"],
    #         roll_max=row["roll_max"],
    #         height_min=row["height_min"],
    #         altitude_max=row["altitude_max"],
    #     )
    #     for index, row in alarms.iterrows()
    # ]


    df.rename(columns={
        "marche": "registration",
        "vcc_min": "vcc_min",
        "vcc_max": "vcc_max",
        "icc_min": "icc_min",
        "icc_max": "icc_max",
        "tint_min": "temperature_box_min",
        "tint_max": "temperature_box_max",
        "gtot_min": "g_tot_min",
        "gtot_max": "g_tot_max",
        "ias_max": "ground_speed_max",
        "vsi_max": "vertical_speed_max",
        "pitch_max": "pitch_max",
        "roll_max": "roll_max",
        "height_min": "height_min",
        "altitude_max": "altitude_max",
    }, inplace=True)
    
    return [
        Alarm(
            registration=row.registration,
            vcc_min=row.vcc_min,
            vcc_max=row.vcc_max,
            icc_min=row.icc_min,
            icc_max=row.icc_max,
            temperature_box_min=row.temperature_box_min,
            temperature_box_max=row.temperature_box_max,
            g_tot_min=row.g_tot_min,
            g_tot_max=row.g_tot_max,
            ground_speed_max=row.ground_speed_max,
            vertical_speed_max=row.vertical_speed_max,
            pitch_max=row.pitch_max,
            roll_max=row.roll_max,
            height_min=row.height_min,
            altitude_max=row.altitude_max,
        )
        for row in df.itertuples(index=False)
    ]


def telemetry_samples_mapper(
    df: pd.DataFrame,
    airplane_datasheets: dict[str:AirplaneDatasheet],
    flight_separator: FlightSeparator,
) -> list[TelemetrySample]:
    telemetry_samples = format_mqtt_message_dataset(df)
    telemetry_samples.sort_values("timestamp", inplace=True)

    # fills missing values using zero-order hold
    telemetry_samples.ffill(inplace=True)
    telemetry_samples.bfill(inplace=True)
    telemetry_samples.replace([float("inf"), -float("inf")], pd.NA, inplace=True)
    telemetry_samples.dropna(inplace=True)

    # Why not only  telemetry_samples.dropna(inplace=True)? 
    # Why include telemetry_samples.ffill(inplace=True) and telemetry_samples.bfill(inplace=True)?

    # telemetry_samples_list = []
    flights_df = flight_separator.get_flights_intervals(telemetry_samples)

    # flights = [
    #   Flight(
    #        stick_on=datetime.fromtimestamp(int(row["stick_on"].timestamp())),
    #        stick_off=datetime.fromtimestamp(int(row["stick_off"].timestamp())),
    #        registration=airplane_datasheets[row["registration"]],
    #   )
    #    for index, row in flights_df.iterrows()
    # ]

    flights = [
        Flight(
            stick_on=datetime.fromtimestamp(int(row.stick_on.timestamp())),
            stick_off=datetime.fromtimestamp(int(row.stick_off.timestamp())),
            registration=airplane_datasheets[row.registration],
        )
        for row in flights_df.itertuples(index=False)
    ]
    # print(flights)

    # for index, row in telemetry_samples.iterrows():
    #     if row["registration"] in airplane_datasheets:
    #         t = TelemetrySample(
    #             unix_timestamp=row["timestamp"],
    #             date_time=datetime.fromtimestamp(row["timestamp"]),
    #             vcc=row["vcc"] if row["vcc"] != "nan" else None,
    #             icc=row["icc"] if row["icc"] != "nan" else None,
    #             temperature_box=(
    #                 row["temperature_box"] if row["temperature_box"] != "nan" else None
    #             ),
    #             magnetic_heading=(
    #                 row["magnetic_heading"]
    #                 if row["magnetic_heading"] != "nan"
    #                 else None
    #             ),
    #             acc_x=row["acc_x"] if row["acc_x"] != "nan" else None,
    #             acc_y=row["acc_y"] if row["acc_y"] != "nan" else None,
    #             acc_z=row["acc_z"] if row["acc_z"] != "nan" else None,
    #             pitch=row["pitch"] if row["pitch"] != "nan" else None,
    #             roll=row["roll"] if row["roll"] != "nan" else None,
    #             turn_rate=row["turn_rate"] if row["turn_rate"] != "nan" else None,
    #             latitude=row["latitude"] if row["latitude"] != "nan" else None,
    #             longitude=row["longitude"] if row["longitude"] != "nan" else None,
    #             altitude=row["altitude"] if row["altitude"] != "nan" else None,
    #             ground_speed=(
    #                 row["ground_speed"] if row["ground_speed"] != "nan" else None
    #             ),
    #             heading=row["heading"] if row["heading"] != "nan" else None,
    #             pressure=row["pressure"] if row["pressure"] != "nan" else None,
    #             pressure_altitude=(
    #                 row["pressure_altitude"]
    #                 if row["pressure_altitude"] != "nan"
    #                 else None
    #             ),
    #             vertical_speed=(
    #                 row["vertical_speed"] if row["vertical_speed"] != "nan" else None
    #             ),
    #         )
    #         telemetry_samples_list.append(t)

    # Replace "nan" strings with None across the entire DataFrame
    telemetry_samples = telemetry_samples.replace("nan", None)

    # Convert the timestamp column to datetime
    telemetry_samples["timestamp"] = pd.to_datetime(telemetry_samples["timestamp"], unit="s")

    # Use itertuples() to iterate over rows
    telemetry_samples_list = [
            TelemetrySample(
                        unix_timestamp=row.timestamp.timestamp(),  # Convert datetime back to UNIX
                        date_time=row.timestamp,                  # Already converted to datetime
                        vcc=row.vcc,
                        icc=row.icc,
                        temperature_box=row.temperature_box,
                        magnetic_heading=row.magnetic_heading,
                        acc_x=row.acc_x,
                        acc_y=row.acc_y,
                        acc_z=row.acc_z,
                        pitch=row.pitch,
                        roll=row.roll,
                        turn_rate=row.turn_rate,
                        latitude=row.latitude,
                        longitude=row.longitude,
                        altitude=row.altitude,
                        ground_speed=row.ground_speed,
                        heading=row.heading,
                        pressure=row.pressure,
                        pressure_altitude=row.pressure_altitude,
                        vertical_speed=row.vertical_speed,
                ) for row in telemetry_samples.itertuples(index=False)    
    ]       
    return telemetry_samples_list, flights
