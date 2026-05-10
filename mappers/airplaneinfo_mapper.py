from datamodels import AirplaneDatasheet


class AirplaneInfoMapper:
    def __init__(self, df_chunk_generator) -> None:
        """
        Constructor for AirplaneInfoMapper.

        This constructor takes a generator of pandas DataFrames as its argument.
        The generator should yield DataFrames containing the columns marche,
        country, typedesignator. The DataFrames can have any number of additional
        columns, but the ones listed above are required.

        Parameters
        ----------
        df_chunk_generator : iter
            A generator of pandas DataFrames.
        """
        self.__chunk_gen = df_chunk_generator

    def __map_single_row(self, row):
        """
        Maps a pandas Series to an AirplaneDatasheet object.

        This method takes a pandas Series as its argument and returns an
        AirplaneDatasheet object. The Series should contain the columns id,
        registration_name, country, typedesignator. The values in these columns
        are used to fill the corresponding attributes in the returned
        AirplaneDatasheet object.

        Parameters
        ----------
        row : pandas.Series
            A pandas Series containing the columns id, registration_name,
            country, typedesignator.

        Returns
        -------
        AirplaneDatasheet
            An AirplaneDatasheet object containing the values from the Series.
        """
        return AirplaneDatasheet(
            id=row["marche"],
            registration_name=row["marche"].strip(),
            country=row["country"],
            typedesignator=row["typedesignator"],
        )

    def generate_airplane_datasheets(self):
        """
        Generates a sequence of AirplaneDatasheet objects from the DataFrames
        yielded by the generator passed in the constructor.

        The generator will yield a sequence of AirplaneDatasheet objects, one
        for each row in the DataFrames. The columns of the DataFrame are used
        to fill the attributes of the AirplaneDatasheet object.

        Yields
        ------
        AirplaneDatasheet
            An AirplaneDatasheet object containing the values from a row in
            the input DataFrames.
        """
        
        # for chunk in self.__chunk_gen:
        #     for index, row in chunk.iterrows():
        #         yield self.__map_single_row(row)
                
        airplaneinfomaps_objects = self.__chunk_gen.apply(self.__map_single_row, axis=1)
        yield from airplaneinfomaps_objects

        # for _, row in self.__chunk_gen.iterrows():
        #     yield self.__map_single_row(row)
