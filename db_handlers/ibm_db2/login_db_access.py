from db_handlers.ibm_db2.db_query_manager import DatabaseManager


class LoginDBAccess:
    def __init__(self, manager: DatabaseManager) -> None:
        self.__manager = manager

    def get_connection_info_by_email_password(self, email: str, password: str):
        query = """
            SELECT *
            FROM MAIN.LOGIN
            WHERE UPPER(USER_EMAIL) = UPPER(?)
              AND USER_PASSWORD = ?
        """
        return self.__manager.get_query_result(query, (email, password))

    def get_connection_info_by_email(self, email: str):
        query = """
            SELECT *
            FROM MAIN.LOGIN
            WHERE UPPER(USER_EMAIL) = UPPER(?)
        """
        return self.__manager.get_query_result(query, (email,))
