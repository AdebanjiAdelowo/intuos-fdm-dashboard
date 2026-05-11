from db_connection_params_handler import ConnectionParamsHandler
from db_handlers.ibm_db2.db_query_manager import DatabaseManager


def make_db_manager(connection: ConnectionParamsHandler) -> DatabaseManager:
    return DatabaseManager(
        username=connection.username,
        password=connection.password,
        ip_address=connection.ip_address,
        port=connection.port,
        db_name=connection.db_name,
    )
