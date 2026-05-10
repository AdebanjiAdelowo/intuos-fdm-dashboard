import joblib
import pandas as pd
import json


class FlightSeparator:

    def __init__(self, model: str, label_names: str, features: str) -> None:
        # Load label_names from JSON file
        with open(label_names, "r") as f:
            label_names = json.load(f)

        # Load model from pickle file
        with open(model, "rb") as f:
            model = joblib.load(f)

        with open(features, "r") as f:
            features_names = json.load(f)

        self.__model = model
        self.__label_names = label_names
        # self.__reverse_label_dict = {v: k for k, v in label_names.items()}
        self.__feature_names = features_names

    def __extract_labeled_samples(self, telemetry_ds: pd.DataFrame) -> pd.DataFrame:
        """
        Process and label telemetry data samples.

        This function takes a DataFrame of telemetry data, performs preprocessing
        steps, and assigns labels using a pre-trained model. The preprocessing
        includes sorting by timestamp, forward and backward filling of missing
        values, and clipping certain feature values to predefined ranges.

        Args:
            telemetry_ds (pd.DataFrame): A DataFrame containing telemetry samples.

        Returns:
            pd.DataFrame: A DataFrame with the same data as the input, but with
            additional columns "label" and "label_names" containing the model's
            predicted labels and their corresponding class names.
        """

        telemetry_ds_labeled = telemetry_ds.copy()
        class_names = {index: value for index, value in enumerate(self.__label_names)}
        telemetry_ds_labeled.sort_values("timestamp", inplace=True)
        telemetry_ds_labeled.ffill(inplace=True)
        telemetry_ds_labeled.bfill(inplace=True)
        telemetry_ds_labeled.dropna(inplace=True)
        telemetry_ds_labeled["acc_y"] = telemetry_ds_labeled["acc_y"].clip(-10, 10)
        telemetry_ds_labeled["pitch"] = telemetry_ds_labeled["pitch"].clip(-180, 180)
        telemetry_ds_labeled["roll"] = telemetry_ds_labeled["roll"].clip(-180, 180)
        telemetry_ds_labeled["altitude"] = telemetry_ds_labeled["altitude"].clip(
            -1, 30_000
        )
        telemetry_ds_labeled["ground_speed"] = telemetry_ds_labeled[
            "ground_speed"
        ].clip(-1, 500)
        telemetry_ds_labeled["vertical_speed"] = telemetry_ds_labeled[
            "vertical_speed"
        ].clip(-5000, 5000)
        X = telemetry_ds_labeled[self.__feature_names].values
        try:
            y = self.__model.predict(X)
        except ValueError:
            y = [[0]] * len(X)
        telemetry_ds_labeled["label"] = y
        telemetry_ds_labeled["label_names"] = telemetry_ds_labeled["label"].map(
            class_names
        )
        return telemetry_ds_labeled

    def get_flights_intervals(
        self, telemetry_ds: pd.DataFrame, minutes_threshold: int = 10
    ) -> pd.DataFrame:
        threshold = minutes_threshold * 60
        telemetry_ds_labeled = self.__extract_labeled_samples(telemetry_ds)

        starts = []
        ends = []

        started = False
        for i in range(1, len(telemetry_ds_labeled)):
            if telemetry_ds_labeled["label_names"].iloc[i] == "flight" and not started:
                starts.append(i)
                started = True

            if started and telemetry_ds_labeled["label_names"].iloc[i] == "taxing":
                ends.append(i)
                started = False

        registration = (
            telemetry_ds_labeled["registration"].iloc[0]
            if len(telemetry_ds_labeled) > 0
            else None
        )
        flights_list = []

        for i in range(len(starts)):
            try:
                if (ends[i] - starts[i]) > threshold:
                    flights_list.append(
                        (
                            telemetry_ds_labeled["datetime"].iloc[starts[i]],
                            telemetry_ds_labeled["datetime"].iloc[ends[i] + 1],
                            registration,
                        )
                    )
            except IndexError:
                pass

        # for flight_start, flight_end, registration in zip(result['datetime'], result['datetime'].shift(-1), result['registration']):
        #     if flight_start is pd.NaT or flight_end is pd.NaT:
        #         continue
        #     # num_samples = len(telemetry_ds[(telemetry_ds['datetime'] >= flight_start) & (telemetry_ds['datetime'] <= flight_end)])
        #     # if num_samples > 100:
        #     flights_list.append((flight_start, flight_end, registration))
        return pd.DataFrame(
            flights_list, columns=["stick_on", "stick_off", "registration"]
        )
