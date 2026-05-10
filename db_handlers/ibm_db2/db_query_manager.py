import pandas as pd
import ibm_db_dbi
from sqlalchemy import create_engine
# import asyncio 
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# from sqlalchemy.orm import sessionmaker


class DatabaseManager:
    def __init__(
        self, username: str, password: str, ip_address: str, port: str, db_name: str
    ) -> None:
        """
        Constructor for DatabaseManager.

        This constructor takes the parameters needed to connect to the DB2 database
        and uses them to create a SQLAlchemy engine.

        Parameters
        ----------
        username : str
            Username to use when connecting to the database.
        password : str
            Password to use when connecting to the database.
        ip_address : str
            IP address of the database server.
        port : str
            Port number to use when connecting to the database.
        db_name : str
            Name of the database to connect to.

        Returns
        -------
        None
        """
        self.__pengine = create_engine(
            f"ibm_db_sa://{username}:{password}@{ip_address}:{port}/{db_name}"
        )
        self.__dsn = (
            f"DATABASE={db_name};"
            f"HOSTNAME={ip_address};"
            f"PORT={port};"
            f"PROTOCOL=TCPIP;"
            f"UID={username};"
            f"PWD={password};"
        )
        try:
            self.__engine = ibm_db_dbi.connect(self.__dsn)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {e}")
        # DATABASE_URL = f"ibm_db_sa+aiodb2://{username}:{password}@{ip_address}:{port}/{db_name}"
        # async_engine = create_async_engine(DATABASE_URL, future=True, echo=True)
        # AsyncSessionLocal = sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)
        # self.dsn = f"ibm_db_sa+aiodb2://{username}:{password}@{ip_address}:{port}/{db_name}"
        # self.engine = create_async_engine(self.dsn, future=True, echo=True)

        
    def get_query_result_generator(self, query: str, chunksize=100_000) -> pd.DataFrame:
        """
        Execute a query and return the result as a generator of pandas DataFrames.

        Each DataFrame in the generator will contain at most `chunksize` rows.

        Parameters
        ----------
        query : str
            SQL query to execute.
        chunksize : int, optional
            Number of rows to include in each DataFrame in the generator. By
            default, 100_000.

        Yields
        ------
        pd.DataFrame
            A pandas DataFrame containing the results of the query, with at most
            `chunksize` rows.
        """
        df = pd.read_sql_query(query, self.__engine, chunksize=chunksize)
        # self.__engine.close()
        return df
    
    def get_query_result(self, query: str) -> pd.DataFrame:
        """
        Execute a query and return the result as a generator of pandas DataFrames.

        Each DataFrame in the generator will contain at most `chunksize` rows.

        Parameters
        ----------
        query : str
            SQL query to execute.

        Yields
        ------
        pd.DataFrame
            A pandas DataFrame containing the results of the query.
        """
        # df = pd.read_sql_query(query, self.__engine)
        
        cursor = self.__engine.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()

        df = pd.DataFrame(rows, columns=[desc[0].lower() for desc in cursor.description])
        # df.columns = df.columns.str.lower()
        # self.__engine.close()
        return df
    
    def get_stored_procedure_result(self, proc_name: str, params: tuple = ()) -> pd.DataFrame:
        """
        Call a stored procedure and return the result as a pandas DataFrame.

        Parameters
        ----------
        proc_name : str
            The name of the stored procedure to call.
        params : tuple, optional
            The parameters to pass to the stored procedure (default is an empty tuple).

        Returns
        -------
        pd.DataFrame
            A pandas DataFrame containing the results of the stored procedure.
        """
        # Build the CALL statement with parameters
        query = f"CALL {proc_name}{params}"
        
        try:
            # Prepare the statement
            #stmt = ibm_db_dbi.prepare(self.__engine, query)
            
            # Execute the statement with parameters
            #ibm_db_dbi.execute(stmt, params)

            # Fetch the result into a pandas DataFrame
            df = pd.read_sql_query(query, self.__engine)
            df.columns = df.columns.str.lower()  # Ensure column names are lowercase
            return df
        except Exception as e:
            raise Exception(f"Error calling stored procedure: {e}")
        
        
    # db_manager = DatabaseManager('username', 'password', 'ip_address', 'port', 'db_name')

    # # Assuming the stored procedure `MY_PROCEDURE` takes two parameters
    # result_df = db_manager.get_stored_procedure_result('MY_PROCEDURE', ('param1_value', 'param2_value'))

    # # Print the result
    # print(result_df)


    
    # async def get_async_query_result(self, query: str) -> pd.DataFrame:
    #     """
    #     Execute an SQL query asynchronously and return a Pandas DataFrame.
    #     """
    #     async with self.engine.begin() as conn:
    #         result = await conn.execute(query)
    #         df = pd.DataFrame(result.fetchall(), columns=result.keys())

    #     # Convert column names to lowercase
    #     df.columns = df.columns.str.lower()
    #     return df
