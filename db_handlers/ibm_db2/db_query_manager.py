import re
from typing import Optional, Sequence


class DatabaseManager:
    def __init__(
        self, username: str, password: str, ip_address: str, port: str, db_name: str
    ) -> None:
        """
        Create DB2 connections used by the data-access layer.

        Query methods accept optional DB-API parameters. Prefer placeholders
        (``?``) plus params over string interpolation for all user-controlled
        values.
        """
        import ibm_db_dbi
        from sqlalchemy import create_engine
        from sqlalchemy.engine import URL

        self.__pengine = create_engine(
            URL.create(
                "ibm_db_sa",
                username=username,
                password=password,
                host=ip_address,
                port=int(port),
                database=db_name,
            )
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

    def get_query_result_generator(
        self, query: str, chunksize: int = 100_000, params: Optional[Sequence] = None
    ):
        """Execute a query and return a generator of pandas DataFrames."""
        import pandas as pd

        return pd.read_sql_query(query, self.__engine, params=params, chunksize=chunksize)

    def get_query_result(self, query: str, params: Optional[Sequence] = None):
        """Execute a query and return a pandas DataFrame."""
        import pandas as pd

        cursor = self.__engine.cursor()
        try:
            cursor.execute(query, params or ())
            rows = cursor.fetchall()
            columns = [desc[0].lower() for desc in cursor.description]
            return pd.DataFrame(rows, columns=columns)
        finally:
            cursor.close()

    def get_stored_procedure_result(self, proc_name: str, params: Optional[Sequence] = None):
        """Call a stored procedure and return the result as a pandas DataFrame."""
        import pandas as pd

        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.]*", proc_name):
            raise ValueError("Invalid stored procedure name")

        params = tuple(params or ())
        placeholders = ", ".join("?" for _ in params)
        query = f"CALL {proc_name}({placeholders})"

        try:
            df = pd.read_sql_query(query, self.__engine, params=params)
            df.columns = df.columns.str.lower()
            return df
        except Exception as e:
            raise RuntimeError(f"Error calling stored procedure {proc_name}: {e}") from e
