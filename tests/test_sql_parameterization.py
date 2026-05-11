from db_handlers.ibm_db2.login_db_access import LoginDBAccess


class DummyManager:
    def __init__(self):
        self.calls = []

    def get_query_result(self, query, params=None):
        self.calls.append((query, params))
        return []


def test_login_query_uses_parameters():
    manager = DummyManager()
    access = LoginDBAccess(manager)

    access.get_connection_info_by_email_password("a@example.com' OR '1'='1", "secret")

    query, params = manager.calls[0]
    assert "?" in query
    assert "a@example.com' OR '1'='1" not in query
    assert params == ("a@example.com' OR '1'='1", "secret")
