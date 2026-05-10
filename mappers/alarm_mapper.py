from datamodels import Alarm


class AlarmMapper:
    def __init__(self, df_chunk_generator) -> None:
        """
        Constructor for AlarmMapper.

        This constructor takes a generator of pandas DataFrames as its argument.
        The generator should yield DataFrames containing the columns
        id, marche, vcc_min, vcc_max, icc_min, icc_max, tint_min, tint_max,
        gtot_min, gtot_max, ias_max, vsi_max, pitch_max, roll_max, height_min,
        altitude_max. The DataFrames can have any number of additional columns,
        but the ones listed above are required.

        Parameters
        ----------
        df_chunk_generator : iter
            A generator of pandas DataFrames.
        """
        self.__chunk_gen = df_chunk_generator

    def __map_single_row(self, row):
        """
        Maps a pandas Series to an Alarm object.

        This method takes a pandas Series as its argument and returns an Alarm
        object. The Series should contain the columns id, marche, vcc_min,
        vcc_max, icc_min, icc_max, tint_min, tint_max, gtot_min, gtot_max,
        ias_max, vsi_max, pitch_max, roll_max, height_min, altitude_max. The
        values in these columns are used to fill the corresponding attributes in
        the returned Alarm object.

        Parameters
        ----------
        row : pandas.Series
            A pandas Series containing the columns id, marche, vcc_min,
            vcc_max, icc_min, icc_max, tint_min, tint_max, gtot_min, gtot_max,
            ias_max, vsi_max, pitch_max, roll_max, height_min, altitude_max.

        Returns
        -------
        Alarm
            An Alarm object containing the values from the Series.
        """
        return Alarm(
            id=row["id"],
            registration_id=row["marche"],
            vcc_min=row["vcc_min"],
            vcc_max=row["vcc_max"],
            icc_min=row["icc_min"],
            icc_max=row["icc_max"],
            temperature_box_min=row["tint_min"],
            temperature_box_max=row["tint_max"],
            g_tot_min=row["gtot_min"],
            g_tot_max=row["gtot_max"],
            ground_speed_max=row["ias_max"],
            vertical_speed_max=row["vsi_max"],
            pitch_max=row["pitch_max"],
            roll_max=row["roll_max"],
            height_min=row["height_min"],
            altitude_max=row["altitude_max"],
        )

    def generate_alarms(self):
        """
        Generates a sequence of Alarm objects from the pandas DataFrames yielded
        by the generator passed in the constructor.

        The generator will yield a sequence of Alarm objects, one for each row in
        the DataFrames. The columns of the DataFrame are used to fill the
        attributes of the Alarm object.

        Parameters
        ----------
        None

        Yields
        -------
        Alarm
            An Alarm object containing the values from the current row in the
            DataFrame.
        """
        # for chunk in self.__chunk_gen:
        #     for _, row in chunk.iterrows():
        #         yield self.__map_single_row(row)
                
        # for _, row in self.__chunk_gen.iterrows():
        #     yield self.__map_single_row(row)

        alarms_objects = self.__chunk_gen.apply(self.__map_single_row, axis=1)
        yield from alarms_objects
