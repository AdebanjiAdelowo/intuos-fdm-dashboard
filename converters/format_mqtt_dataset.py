import pandas as pd


def format_mqtt_message_dataset(df: pd.DataFrame) -> pd.DataFrame:
    df_n_channel = df[df["mqtt_channel"] == "N"]
    df_n_channel = df_n_channel[
        ["datetime_message", "mqtt_subtopic", "payload_alfa", "marche"]
    ]

    datetime_format = "%Y-%m-%d-%H.%M.%S.%f"

    df_n_channel["timestamp"] = (
        pd.to_datetime(df_n_channel["datetime_message"], format=datetime_format)
        .map(pd.Timestamp.timestamp)
        .astype(int)
    )
    
    df_n_channel.sort_values(by="timestamp", inplace=True)
    df_n_channel.set_index("timestamp", inplace=True)

    current_timestamp = 0
    current_row = [None] * 21
    row_list = []
    
    for index, row in df_n_channel.iterrows():

        if index > current_timestamp:
            row_list.append(current_row)
            current_timestamp = index
            current_row = [None] * 21
            current_row[0] = index
            current_row[1] = row["datetime_message"]
            current_row[20] = row["marche"]
            
        if row["mqtt_subtopic"] == "0":
            try:
                current_row[2] = (
                    float(row["payload_alfa"])
                    if abs(float(row["payload_alfa"])) < 1000
                    else pd.NA
                )
            except ValueError:
                # print(f'0:{row["payload_alfa"]}')
                pass
        if row["mqtt_subtopic"] == "1":
            try:
                current_row[3] = (
                    float(row["payload_alfa"])
                    if abs(float(row["payload_alfa"])) < 1000
                    else pd.NA
                )
            except ValueError:
                # print(f'1:{row["payload_alfa"]}')
                pass
        if row["mqtt_subtopic"] == "2":
            try:
                current_row[4] = (
                    float(row["payload_alfa"])
                    if abs(float(row["payload_alfa"])) < 1000
                    else pd.NA
                )
            except ValueError:
                # print(f'2:{row["payload_alfa"]}')
                pass
        if row["mqtt_subtopic"] == "5":
            try:
                current_row[5] = (
                    float(row["payload_alfa"])
                    if abs(float(row["payload_alfa"])) < 360
                    else pd.NA
                )
            except ValueError:
                # print(f'5:{row["payload_alfa"]}')
                pass
            
        if row["mqtt_subtopic"] == "6":
            payload_string_list = row["payload_alfa"]
            try:
                current_row[9] = (
                    int(payload_string_list[0:4])
                    if abs(int(payload_string_list[0:4])) < 180
                    else pd.NA
                )
                current_row[10] = (
                    int(payload_string_list[4:8])
                    if abs(int(payload_string_list[4:8])) < 180
                    else pd.NA
                )
                current_row[6] = (
                    float(payload_string_list[8:13])
                    if abs(float(payload_string_list[8:13])) < 9
                    else pd.NA
                    
                )
                current_row[7] = (
                    float(payload_string_list[13:18])
                    if abs(float(payload_string_list[13:18])) < 9
                    else pd.NA
                )
                current_row[8] = (
                    float(payload_string_list[18:23])
                    if abs(float(payload_string_list[18:23])) < 9
                    else pd.NA
                )
                current_row[11] = (
                    int(payload_string_list[23:])
                    if abs(int(payload_string_list[23:])) < 180
                    else pd.NA
                )
            except ValueError:
                # print(f'6:{row["payload_alfa"]}')
                pass

        if row["mqtt_subtopic"] == "7":
            try:
                payload_string_list = row["payload_alfa"].split(",")
                if payload_string_list[5] == "1":
                    lat, lon, alt = (
                        float(payload_string_list[0]),
                        float(payload_string_list[1]),
                        float(payload_string_list[2]),
                    )
                    alt = pd.NA if alt > 10_000 else alt
                    current_row[12] = float(lat) if abs(float(lat)) < 90 else pd.NA
                    current_row[13] = float(lon) if abs(float(lon)) < 180 else pd.NA
                    current_row[14] = float(alt) if abs(float(alt)) < 100_000 else pd.NA
                    current_row[15] = (
                        float(payload_string_list[3])
                        if float(payload_string_list[3]) < 1000
                        else pd.NA
                    )
                    current_row[16] = (
                        float(payload_string_list[4])
                        if abs(float(payload_string_list[4])) < 1000
                        else pd.NA
                    )
            except:
                # print(f'7:{row["payload_alfa"]}')
                pass

        if row["mqtt_subtopic"] == "9":
            payload_string_list = row["payload_alfa"].split(",")
            if len(payload_string_list) == 2:
                try:
                    current_row[17] = (
                        float(payload_string_list[0])
                        if float(payload_string_list[0]) < 10000
                        else pd.NA
                    )
                    current_row[18] = (
                        float(payload_string_list[1])
                        if float(payload_string_list[1]) < 10000
                        else pd.NA
                    )
                except ValueError:
                    pass                
            if len(payload_string_list) == 1:
                try:
                    current_row[17] = (
                        float(payload_string_list[0])
                        if float(payload_string_list[0]) < 10000
                        else pd.NA
                    )
                except ValueError:
                    pass

        if row["mqtt_subtopic"] == "V":
            try:
                current_row[19] = (
                    float(row["payload_alfa"])
                    if float(row["payload_alfa"]) < 10000
                    else pd.NA
                )
            except ValueError:
                # print(f'V:{row["payload_alfa"]}')
                pass
            
    formatted_df = pd.DataFrame(
        row_list[1:],
        columns=[
            "timestamp",
            "datetime",
            "vcc",
            "icc",
            "temperature_box",
            "magnetic_heading",
            "acc_x",
            "acc_y",
            "acc_z",
            "pitch",
            "roll",
            "turn_rate",
            "latitude",
            "longitude",
            "altitude",
            "ground_speed",
            "heading",
            "pressure",
            "pressure_altitude",
            "vertical_speed",
            "registration",
        ],
    )

    return formatted_df
