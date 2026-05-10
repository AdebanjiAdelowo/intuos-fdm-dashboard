import copy
import pandas as pd
import numpy as np
from datamodels import TelemetrySample
from logic.alarm_assignment import AlarmHandlerDF
from logic.position_assignment import PositionAssigner
import types


class UnformattedTelemetryMapper:
    def __init__(
        self,
        df_chunk_generator: iter,
        position_assigner: PositionAssigner,
        alarm_assigner: AlarmHandlerDF = None,
    ) -> None:
        self.__chunk_gen = df_chunk_generator
        self._previous_telemetry_sample = TelemetrySample()
        self._position_assigner = position_assigner
        self._alarm_assigner = alarm_assigner

    def __format_mqtt_message_chunk(self, df: pd.DataFrame) -> pd.DataFrame:
        df_ne_channel = df[(df["mqtt_channel"] == "N") | (df["mqtt_channel"] == "E")]
        df_ne_channel = df_ne_channel[
            [
                "datetime_message",
                "mqtt_channel",
                "mqtt_subtopic",
                "payload_alfa",
                "marche",
            ]
        ]

        datetime_format = "%Y-%m-%d-%H.%M.%S.%f"

        df_ne_channel["timestamp"] = (
            pd.to_datetime(df_ne_channel["datetime_message"], format=datetime_format)
            .map(pd.Timestamp.timestamp)
            .astype(int)
        )
        df_ne_channel.sort_values(by="timestamp", inplace=True)
        df_ne_channel.set_index("timestamp", inplace=True)

        current_timestamp = 0
        current_row = [None] * 21
        row_list = []
        
        for index, row in df_ne_channel.iterrows():
            if index > current_timestamp:
                row_list.append(current_row)
                current_timestamp = index
                current_row = [None] * 22
                current_row[0] = index
                current_row[1] = row["datetime_message"]
                current_row[21] = row["marche"]
            if row["mqtt_subtopic"] == "0":
                try:
                    current_row[2] = (
                        float(row["payload_alfa"])
                        if abs(float(row["payload_alfa"])) < 1000
                        else 0
                    )
                except ValueError:
                    # print(f'0:{row["payload_alfa"]}')
                    pass
            if row["mqtt_subtopic"] == "1":
                try:
                    current_row[3] = (
                        float(row["payload_alfa"])
                        if abs(float(row["payload_alfa"])) < 1000
                        else 0
                    )
                except ValueError:
                    # print(f'1:{row["payload_alfa"]}')
                    pass
            if row["mqtt_subtopic"] == "2":
                try:
                    current_row[4] = (
                        float(row["payload_alfa"])
                        if abs(float(row["payload_alfa"])) < 1000
                        else 0
                    )
                except ValueError:
                    # print(f'2:{row["payload_alfa"]}')
                    pass
            if row["mqtt_subtopic"] == "5":
                try:
                    current_row[5] = (
                        float(row["payload_alfa"])
                        if abs(float(row["payload_alfa"])) < 360
                        else 0
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
                        else 0
                    )
                    current_row[10] = (
                        int(payload_string_list[4:8])
                        if abs(int(payload_string_list[4:8])) < 180
                        else 0
                    )
                    current_row[7] = (
                        float(payload_string_list[8:13])
                        if abs(float(payload_string_list[8:13])) < 9
                        else 0
                    )
                    current_row[6] = (
                        float(payload_string_list[13:18])
                        if abs(float(payload_string_list[13:18])) < 9
                        else 0
                    )
                    current_row[8] = (
                        float(payload_string_list[18:23])
                        if abs(float(payload_string_list[18:23])) < 9
                        else 0
                    )
                    current_row[11] = (
                        int(payload_string_list[23:])
                        if abs(int(payload_string_list[23:])) < 180
                        else 0
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
                        alt = 0 if alt > 10_000 else alt
                        current_row[12] = float(lat) if abs(float(lat)) < 90 else 0
                        current_row[13] = float(lon) if abs(float(lon)) < 180 else 0
                        current_row[14] = float(alt) if abs(float(alt)) < 100_000 else 0
                        current_row[15] = (
                            float(payload_string_list[3])
                            if float(payload_string_list[3]) < 1000
                            else 0
                        )
                        current_row[16] = (
                            float(payload_string_list[4])
                            if abs(float(payload_string_list[4])) < 1000
                            else 0
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
                            else 0
                        )
                        current_row[18] = (
                            float(payload_string_list[1])
                            if float(payload_string_list[1]) < 10000
                            else 0
                        )
                    except ValueError:
                        pass
                if len(payload_string_list) == 1:
                    try:
                        current_row[17] = (
                            float(payload_string_list[0])
                            if float(payload_string_list[0]) < 10000
                            else 0
                        )
                    except ValueError:
                        pass

            if row["mqtt_subtopic"] == "V":
                try:
                    current_row[19] = (
                        float(row["payload_alfa"])
                        if float(row["payload_alfa"]) < 10000
                        else 0
                    )
                except ValueError:
                    # print(f'V:{row["payload_alfa"]}')
                    pass

            if row["mqtt_channel"] == "E":
                try:
                    current_row[20] = (
                        float(row["payload_alfa"])
                        if abs(float(row["payload_alfa"])) < 1000
                        else 0
                    )
                except ValueError:
                    # print(f'E:{row["payload_alfa"]}')
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
                "elevation",
                "registration",
            ],
        )

        return formatted_df

    def __interpolate_zero_hold(self, df: pd.DataFrame) -> pd.DataFrame:
        df.replace([float("inf"), -float("inf")], pd.NA, inplace=True)
        df.ffill(inplace=True)
        df.bfill(inplace=True)
        df.dropna(inplace=True)
        return df

    def generate_telemetry_samples(self):
        # for chunk in self.__chunk_gen:
        #     data = self.__format_mqtt_message_chunk(chunk)
        #     data = self.__interpolate_zero_hold(data)
        #     data = self._position_assigner.assign_positions_to_telemetry(data)
        #     for row in data.itertuples():
        #         yield self.__map_single_row(row)
                   
        data = self.__format_mqtt_message_chunk(self.__chunk_gen)
        data = self.__interpolate_zero_hold(data)
        data = self._position_assigner.assign_positions_to_telemetry(data)
        for row in data.itertuples():
            yield self.__map_single_row(row)
                

    def __map_single_row(self, row) -> TelemetrySample:
        sample = (
            copy.deepcopy(self._previous_telemetry_sample)
            if self._previous_telemetry_sample
            else TelemetrySample()
        )
        sample.clear_alarms()
        sample.id = row["timestamp"]
        sample.unix_timestamp = row["timestamp"]
        sample.date_time = row["datetime"]
        sample.vcc = row["vcc"]
        sample.icc = row["icc"]
        sample.temperature_box = row["temperature_box"]
        sample.magnetic_heading = row["magnetic_heading"]
        sample.acc_x = row["acc_x"]
        sample.acc_y = row["acc_y"]
        sample.acc_z = row["acc_z"]
        sample.pitch = row["pitch"]
        sample.roll = row["roll"]
        sample.turn_rate = row["turn_rate"]
        sample.latitude = row["latitude"]
        sample.longitude = row["longitude"]
        sample.altitude = row["altitude"]
        sample.ground_speed = row["ground_speed"]
        sample.heading = row["heading"]
        sample.pressure = row["pressure"]
        sample.pressure_altitude = row["pressure_altitude"]
        sample.vertical_speed = row["vertical_speed"]
        sample.height = row["altitude"] - row["elevation"]
        sample.elevation = row["elevation"]
        sample.registration_id = row["registration"]
        sample.attitude = row["attitude"]
        self._previous_telemetry_sample = sample
        return sample


class FormattedTelemetryMapper:
    def __init__(
        self, df_chunk_generator: pd.DataFrame, position_assigner: PositionAssigner
    ) -> None:
        """
        Constructor for FormattedTelemetryMapper.

        This constructor takes a generator of pandas DataFrames and a
        PositionAssigner object as its arguments. The generator should yield
        DataFrames containing the columns vcc, icc, temperature_box,
        magnetic_heading, acc_x, acc_y, acc_z, pitch, roll, turn_rate,
        latitude, longitude, altitude, ground_speed, heading, pressure,
        pressure_altitude, vertical_speed, elevation, registration_id,
        attitude. The DataFrames can have any number of additional columns, but
        the ones listed above are required.

        Parameters
        ----------
        df_chunk_generator : iter
            A generator of pandas DataFrames.
        position_assigner : PositionAssigner
            A PositionAssigner object used to assign labels to the telemetry
            samples.

        After initialization, the object is ready to be used to map telemetry
        samples to TelemetrySample objects using the generate_telemetry_samples
        method.
        """
        self.__chunk_gen = df_chunk_generator
        self._previous_telemetry_sample = None
        self._position_assigner = position_assigner

    def __format_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Format a DataFrame of telemetry data into the format expected by the
        PositionAssigner.

        This function takes a DataFrame of telemetry data and formats it into
        the format expected by the PositionAssigner. The DataFrame should have
        columns with the names date_time, vcc, icc, temperature_box,
        magnetic_heading, acc_x, acc_y, acc_z, pitch, roll, turn_rate,
        latitude, longitude, altitude, ground_speed, heading, pressure,
        pressure_altitude, vertical_speed, elevation, registration_id.

        The output of this function is a DataFrame with the same columns, but
        with the date_time column converted to a unix timestamp (in seconds) and
        the vcc, icc, temperature_box, magnetic_heading, acc_x, acc_y, acc_z,
        pitch, roll, turn_rate, latitude, longitude, altitude, ground_speed,
        heading, pressure, pressure_altitude, vertical_speed, elevation columns
        converted to floats. The registration_id column is copied from the
        marche column of the input DataFrame.

        The function also drops any duplicate rows of the DataFrame, keeping
        only the last row of each set of duplicates.

        Parameters
        ----------
        df : pd.DataFrame
            A DataFrame of telemetry data.

        Returns
        -------
        pd.DataFrame
            A DataFrame of telemetry data in the format expected by the
            PositionAssigner.
        """
        df["timestamp"] = pd.to_datetime(df["date_time"], unit="s").astype(np.int64) // 10**9
        
        # new_df['vcc'] = pd.to_numeric(df['vcc'], errors='coerce').astype(float)
        # new_df['icc'] = pd.to_numeric(df['icc'], errors='coerce').astype(float)
        # new_df['temperature_box'] = pd.to_numeric(df['temperature_box'], errors='coerce').astype(float)
        properties = [
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
            "vertical_speed",
            "elevation"
            # "height"
        ]
        try:
            df[properties] = df[properties].apply(lambda x: pd.to_numeric(x, errors="coerce").astype(float))
        except ValueError as e:
            print(e)
            
        # try:
        #     for props in properties:
        #         new_df[props] = pd.to_numeric(df[props], errors="coerce").astype(float)
        # except ValueError as e:
        
        df.rename(columns={"marche":"registration", "date_time":"datetime"}, inplace=True)
 
        # new_df["registration"] = df["marche"]
        #  new_df["datetime"] = df["date_time"]
        # new_df = new_df.drop_duplicates(subset=["timestamp"], keep="last")
        # df.drop_duplicates(subset=["timestamp"], keep="last", inplace=True)
        properties.extend(["registration","timestamp", "datetime"])
        return df[properties]

    def __interpolate_zero_hold(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fill NaN values in the given DataFrame using a zero-order hold.

        This function takes a DataFrame and fills any NaN values in it by
        propagating the last valid value forward. This is done using the
        "ffill" and "bfill" methods of the DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            A DataFrame of telemetry data.

        Returns
        -------
        pd.DataFrame
            A DataFrame of telemetry data with any NaN values filled in.
        """
        df = df.replace([float("inf"), -float("inf")], pd.NA)
        df = df.ffill()
        df = df.bfill()
        # df.dropna(inplace=True)
        return df
    def generate_telemetry_samples(self):
        """
        Generate a sequence of telemetry samples from a sequence of DataFrames.

        This generator takes no arguments and yields a sequence of TelemetrySample
        objects. The sequence is infinite and will yield a TelemetrySample object
        for each row in each DataFrame in the sequence provided in the
        constructor.

        The generator will perform the following operations on each DataFrame in
        the sequence:

        1. Format the DataFrame into the correct columns using the
           __format_dataframe method.
        2. Fill any NaN values in the DataFrame using the
           __interpolate_zero_hold method.
        3. Assign positions to the telemetry samples using the
           assign_positions_to_telemetry method of the PositionAssigner object
           passed in the constructor.
        4. Yield a TelemetrySample object for each row in the DataFrame using
           the __map_single_row method.

        Yields
        ------
        TelemetrySample
            A TelemetrySample object containing the values from a row in the
            input DataFrame.
        """    
        data = self.__format_dataframe(self.__chunk_gen)
        data = self.__interpolate_zero_hold(data)
        data = self._position_assigner.assign_positions_to_telemetry(data)
        data['unix_timestamp'] = data['timestamp']
        data.rename(columns={'timestamp':'id', 'datetime':'date_time'}, inplace=True)
        for row in data.itertuples():
            yield self.__map_single_row(row)
                
    def new_generate_telemetry_samples(self):
        """
        Generate a sequence of telemetry samples from a sequence of DataFrames.

        This generator takes no arguments and yields a sequence of TelemetrySample
        objects. The sequence is infinite and will yield a TelemetrySample object
        for each row in each DataFrame in the sequence provided in the
        constructor.

        The generator will perform the following operations on each DataFrame in
        the sequence:

        1. Format the DataFrame into the correct columns using the
           __format_dataframe method.
        2. Fill any NaN values in the DataFrame using the
           __interpolate_zero_hold method.
        3. Assign positions to the telemetry samples using the
           assign_positions_to_telemetry method of the PositionAssigner object
           passed in the constructor.
        4. Yield a TelemetrySample object for each row in the DataFrame using
           the __map_single_row method.

        Yields
        ------
        TelemetrySample
            A TelemetrySample object containing the values from a row in the
            input DataFrame.
        """

        data = self.__format_dataframe(self.__chunk_gen)
        data = self.__interpolate_zero_hold(data)
        data = self._position_assigner.assign_positions_to_telemetry(data)
        data['unix_timestamp'] = data['timestamp']
        data['height'] =  data['altitude'] - data['elevation']
        data.rename(columns={'timestamp':'id', 'datetime':'date_time', 'registration':'registration_id'}, inplace=True)
        # data['height'] = data['altitude'] - data['elevation']
        return data

    def generate_telemetry_alarms(self, has_alarms=False):
        telemetry_alarms_samples = self.new_generate_telemetry_samples()
        alarm_mapping = {
            'alarm_g_tot': 'g_tot',
            'alarm_ground_speed': 'ground_speed',
            'alarm_vertical_speed': 'vertical_speed',
            'alarm_pitch': 'pitch',
            'alarm_roll': 'roll',
            'alarm_altitude': 'altitude',
            'alarm_hard_landing': 'hard_landing',
            'alarm_high_roll_at_low_height': 'high_roll_at_low_height',
            'alarm_low_ground_speed_at_low_height_with_low_acceleration': 'low_ground_speed_at_low_height_with_low_acceleration',
            'alarm_high_pitch_at_low_height_with_low_acceleration': 'high_pitch_at_low_height_with_low_acceleration'
        }

        def merge_alarms(row):
            return [alarm_mapping[col] for col in alarm_mapping if row[col] == 1]

        telemetry_alarms_samples['alarms'] = self.__chunk_gen.apply(merge_alarms, axis=1)   
        telemetry_alarms_samples = telemetry_alarms_samples.sort_values(by='unix_timestamp', ascending=True)
        if has_alarms:
            telemetry_alarms_samples = telemetry_alarms_samples[telemetry_alarms_samples['alarms'].apply(lambda x: len(x) > 0)]
        telemetry_objects = telemetry_alarms_samples.apply(self.create_telemetry_sample, axis=1)
        return telemetry_objects

    def create_telemetry_sample(self, row):
        sample = TelemetrySample()
        sample.id = row['id']
        sample.unix_timestamp = row['unix_timestamp']
        sample.date_time = row['date_time']
        sample.registration_id = row['registration_id']
        sample.magnetic_heading = row['magnetic_heading']
        sample.longitude = row['longitude']
        sample.altitude = row['altitude']
        sample.attitude = row['attitude']
        sample.latitude = row['latitude']
        sample.alarms = row['alarms']
        sample.acc_x = row['acc_x']
        sample.acc_y = row['acc_y']
        sample.acc_z = row['acc_z']
        sample.pitch = row['pitch']
        sample.roll = row['roll']
        sample.turn_rate = row['turn_rate']
        sample.ground_speed = row['ground_speed']
        sample.heading = row['heading']
        sample.vertical_speed = row['vertical_speed']
        sample.height = row['height']
        sample.elevation = row['elevation']
        return sample
        
    def __map_single_row(self, row) -> TelemetrySample:
        """
        Maps a pandas Series to a TelemetrySample object.

        This method takes a pandas Series as its argument and returns a TelemetrySample
        object. The Series should contain the columns id_volo, data_ora_decollo,
        data_ora_atterraggio, marche, apt_takeoff, apt_landing. The values in these
        columns are used to fill the corresponding attributes in the returned
        TelemetrySample object.

        The method will also fill any NaN values in the input Series using the
        __interpolate_zero_hold method of the PositionAssigner object passed in the
        constructor.

        Parameters
        ----------
        row : pandas.Series
            A pandas Series containing the columns id_volo, data_ora_decollo,
            data_ora_atterraggio, marche, apt_takeoff, apt_landing.

        Returns
        -------
        TelemetrySample
            A TelemetrySample object containing the values from the Series.
        """
        # sample = (
        #     copy.deepcopy(self._previous_telemetry_sample)
        #     if self._previous_telemetry_sample
        #     else TelemetrySample()
        # )
        # sample.clear_alarms()
        sample = TelemetrySample()
        sample.id = row.id
        sample.unix_timestamp = row.unix_timestamp
        sample.date_time = row.date_time
        # sample.vcc = row.vcc
        # sample.icc = row.icc
        # sample.temperature_box = row.temperature_box
        sample.magnetic_heading = row.magnetic_heading
        sample.acc_x = row.acc_x
        sample.acc_y = row.acc_y
        sample.acc_z = row.acc_z
        sample.pitch = row.pitch
        sample.roll = row.roll
        sample.turn_rate = row.turn_rate
        sample.latitude = row.latitude
        sample.longitude = row.longitude
        sample.altitude = row.altitude
        sample.ground_speed = row.ground_speed
        sample.heading = row.heading
        # sample.pressure = row.pressure
        # sample.pressure_altitude = row.pressure_altitude
        sample.vertical_speed = row.vertical_speed
        sample.height = float(row.altitude) - float(row.elevation)
        sample.elevation = row.elevation
        sample.registration_id = row.registration
        sample.attitude = row.attitude
        # self._previous_telemetry_sample = sample
        return sample