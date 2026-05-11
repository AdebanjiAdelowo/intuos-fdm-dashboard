import os

from db_connection_params_handler import ConnectionParamsHandler


def test_connection_params_can_load_from_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_USERNAME", "user")
    monkeypatch.setenv("DATABASE_PASSWORD", "password")
    monkeypatch.setenv("DATABASE_HOST", "db.example.test")
    monkeypatch.setenv("DATABASE_PORT", "50000")
    monkeypatch.setenv("DATABASE_NAME", "SAMPLE")

    config = ConnectionParamsHandler.from_environment()

    assert config.username == "user"
    assert config.password == "password"
    assert config.ip_address == "db.example.test"
    assert config.port == "50000"
    assert config.db_name == "SAMPLE"


def test_connection_params_file_fallback(tmp_path):
    config_file = tmp_path / "config.yml"
    config_file.write_text(
        "database:\n"
        "  username: file-user\n"
        "  password: file-password\n"
        "  ip_address: file-host\n"
        "  port: '50000'\n"
        "  db_name: FILEDB\n"
    )

    config = ConnectionParamsHandler(connection_filename=str(config_file))

    assert config.username == "file-user"
    assert config.password == "file-password"
    assert config.ip_address == "file-host"
    assert config.port == "50000"
    assert config.db_name == "FILEDB"
