import json
import joblib
import pandas as pd


class PositionAssigner:
    def __init__(
        self, model_file_path: str, label_names_file_path: str, features_file_path: str
    ) -> None:
        """
        Initialize a PositionAssigner object.

        Args:
        model_file_path (str): the path to a joblib dump of a scikit-learn model
        label_names_file_path (str): the path to a JSON file containing a dict mapping
            integer labels to their string names
        features_file_path (str): the path to a JSON file containing a list of the names
            of the features used in the model

        The model is expected to be a scikit-learn classifier, and the features_file_path
        is expected to contain the names of the features in the order they are expected
        by the model.

        After initialization, the object is ready to be used to assign positions to
        telemetry samples using the assign_position method.

        """
        with open(label_names_file_path, "r") as f:
            label_names = json.load(f)

        with open(model_file_path, "rb") as f:
            model = joblib.load(f)

        with open(features_file_path, "r") as f:
            features_names = json.load(f)

        self.__model = model
        self.__reverse_label_dict = {v: k for k, v in label_names.items()}
        self.__feature_names = features_names

    def assign_positions_to_telemetry(self, telemetry_ds: pd.DataFrame) -> pd.DataFrame:
        """
        Assign a position to each telemetry sample in telemetry_ds.

        Args:
        telemetry_ds (pd.DataFrame): a DataFrame containing telemetry samples

        Returns:
        pd.DataFrame: a DataFrame with the same columns as telemetry_ds, plus a
            column named "label" containing the integer labels of the positions
            assigned to the samples and a column named "attitude" containing the
            string names of the positions

        The model used to assign positions is the one that was specified in the
        constructor of this object.

        """
        if telemetry_ds.empty:
            return telemetry_ds
        X = telemetry_ds[self.__feature_names].values
        y = self.__model.predict(X)
        telemetry_ds_labeled = telemetry_ds
        telemetry_ds_labeled["label"] = y
        telemetry_ds_labeled["attitude"] = telemetry_ds_labeled["label"].map(
            self.__reverse_label_dict
        )
        return telemetry_ds_labeled
