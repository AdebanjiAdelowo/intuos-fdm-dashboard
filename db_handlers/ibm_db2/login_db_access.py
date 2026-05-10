from db_handlers.ibm_db2.db_query_manager import DatabaseManager


class LoginDBAccess:
    def __init__(self, manager: DatabaseManager) -> None:
        self.__manager = manager

    def get_connection_info_by_email_password(self, email: str, password: str) -> bool:
        query = f"SELECT * FROM MAIN.LOGIN WHERE UPPER(USER_EMAIL) = UPPER('{email}') AND USER_PASSWORD = '{password}'"
        result = self.__manager.get_query_result(query)
        return result

    def get_connection_info_by_email(self, email: str):
        query = f"SELECT * FROM MAIN.LOGIN WHERE UPPER(USER_EMAIL) = UPPER('{email}')"
        result = self.__manager.get_query_result(query)
        return result
