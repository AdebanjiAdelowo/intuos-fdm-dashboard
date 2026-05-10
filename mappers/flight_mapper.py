from datamodels import Flight


class FlightMapper:
    def __init__(self, df_chunk_generator: iter):
        """
        Constructor for FlightMapper.

        This constructor takes a generator of pandas DataFrames as its argument.
        The generator should yield DataFrames containing the columns
        id_volo, data_ora_decollo, data_ora_atterraggio, marche, apt_takeoff,
        apt_landing. The DataFrames can have any number of additional columns,
        but the ones listed above are required.

        Parameters
        ----------
        df_chunk_generator : iter
            A generator of pandas DataFrames.
        """
        self.__chunk_gen = df_chunk_generator

    def __map_single_row(self, row):
        """
        Maps a pandas Series to a Flight object.

        This method takes a pandas Series as its argument and returns a Flight
        object. The Series should contain the columns id_volo, data_ora_decollo,
        data_ora_atterraggio, marche, apt_takeoff, apt_landing. The values in
        these columns are used to fill the corresponding attributes in the
        returned Flight object.

        Parameters
        ----------
        row : pandas.Series
            A pandas Series containing the columns id_volo, data_ora_decollo,
            data_ora_atterraggio, marche, apt_takeoff, apt_landing.

        Returns
        -------
        Flight
            A Flight object containing the values from the Series.
        """
        return Flight(
            id=row["id_volo"],
            stick_on=row["data_ora_decollo"],
            stick_off=row["data_ora_atterraggio"],
            registration_id=row["marche"],
            airport_takeoff=row["apt_takeoff"],
            airport_landing=row["apt_landing"],
        )

    def generate_converted_flights(self):
        """
        Generates a sequence of Flight objects from the DataFrames in the
        generator provided in the constructor.

        This method takes no arguments and returns a generator of Flight objects.
        The generator is infinite and will yield a Flight object for each row in
        each DataFrame in the input generator.

        Yields
        ------
        Flight
            A Flight object containing the values from a row in the input
            DataFrames.
        """
        
        # for chunk in self.__chunk_gen:
        #       for _, row in chunk.iterrows():
        #           yield self.__map_single_row(row)

        # for chunk in self.__chunk_gen:
        #      # Use apply to map each row to a Flight object
        #      flight_objects = chunk.apply(self.__map_single_row, axis=1)
        #      # Yield each Flight object
        #      yield from flight_objects
                
        # for _, row in self.__chunk_gen.iterrows():
        #       yield self.__map_single_row(row)

        flight_objects = self.__chunk_gen.apply(self.__map_single_row, axis=1)
        return flight_objects
        #yield from flight_objects
