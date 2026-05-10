from datamodels import PilotDatasheet

        
class PilotInfoMapper:
    def __init__(self, df_chunk_generator) -> None:
        """
        Constructor for PilotInfoMapper.

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
        codcf = row["codcf"].strip()
        ragsoc = row["ragsoc1"].strip() if row["ragsoc1"] is not None else ""
        nato = row["natonazcf"].strip() if row["natonazcf"] is not None else ""
        inst = row["istrusn"].strip()   if row["istrusn"] is not None else ""
        stud = row["studentsn"].strip() if row["studentsn"] is not None else ""
        return PilotDatasheet(id=codcf,pilot_name=ragsoc,nationality=nato,instructor=inst, student=stud)

    def generate_pilot_datasheets(self):
        """
        Generates a sequence of PilotDatasheet objects from the DataFrames
        yielded by the generator passed in the constructor.

        The generator will yield a sequence of PilotDatasheet objects, one
        for each row in the DataFrames. The columns of the DataFrame are used
        to fill the attributes of the PilotDatasheet object.

        Yields
        ------
        PilotDatasheet
            An PilotDatasheet object containing the values from a row in
            the input DataFrames.
        """
        
        # for chunk in self.__chunk_gen:
        #     for index, row in chunk.iterrows():
        #         yield self.__map_single_row(row)
                
        pilotinfomaps_objects = self.__chunk_gen.apply(self.__map_single_row, axis=1)
        yield from pilotinfomaps_objects

        # for _, row in self.__chunk_gen.iterrows():
        #     yield self.__map_single_row(row)
