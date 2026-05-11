class UserDBAccess:
    def __init__(self, manager):
        self._manager = manager

    def get_all_users(self):
        query = "SELECT * FROM ANA.ANACLI"
        return self._manager.get_query_result(query)

    def get_user_by_codcf(self, codcf: str):
        query = """
            SELECT CODCF, STUDENTSN, EMAIL, TELEFONO1, TELEFONO2
            FROM ANA.ANACLI
            WHERE CODCF = ?
        """
        return self._manager.get_query_result(query, (codcf,))
