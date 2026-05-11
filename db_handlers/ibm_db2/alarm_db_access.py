from db_handlers.ibm_db2.db_query_manager import DatabaseManager


class AlarmDBAccess:
    def __init__(self, manager: DatabaseManager) -> None:
        self.__manager = manager

    def get_all_alarms(self):
        query = "SELECT * FROM BASE.BOX_ALARM"
        return self.__manager.get_query_result(query)

    def get_alarm_by_marca(self, marca: str):
        query = "SELECT * FROM BASE.BOX_ALARM WHERE MARCHE = ?"
        return self.__manager.get_query_result(query, (marca,))
