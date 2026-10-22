import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, text
from sqlalchemy.exc import StatementError

from app.core.config import Settings, settings
from app.core.database import engine


def test_jwt_secret_is_required(monkeypatch):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)
    assert error.value.errors()[0]["loc"] == ("JWT_SECRET_KEY",)


@pytest.mark.parametrize("secret", ["", " " * 32, "short-secret", "a" * 31])
def test_invalid_jwt_secret_is_rejected_without_printing_it(secret):
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, JWT_SECRET_KEY=secret)
    assert "input_value" not in str(error.value)


@pytest.mark.parametrize("secret", ["a" * 32, "é" * 16])
def test_jwt_secret_uses_utf8_byte_length(secret):
    config = Settings(_env_file=None, JWT_SECRET_KEY=secret)
    assert config.JWT_SECRET_KEY.get_secret_value() == secret
    assert secret not in repr(config)


def test_sql_echo_defaults_to_false(monkeypatch):
    monkeypatch.delenv("SQL_ECHO", raising=False)
    assert Settings(_env_file=None).SQL_ECHO is False


@pytest.mark.parametrize("value,expected", [("true", True), ("false", False)])
def test_sql_echo_reads_environment(monkeypatch, value, expected):
    monkeypatch.setenv("SQL_ECHO", value)
    assert Settings(_env_file=None).SQL_ECHO is expected


def test_application_engine_hides_parameters():
    assert engine.echo == settings.SQL_ECHO
    assert engine.hide_parameters is True


def test_sql_debug_log_hides_bound_values(caplog):
    debug_engine = create_engine("sqlite://", echo=True, hide_parameters=True)
    secret = "sensitive-bound-value"
    try:
        with debug_engine.connect() as connection:
            assert connection.execute(text("SELECT :value"), {"value": secret}).scalar_one() == secret
            with pytest.raises(StatementError) as error:
                connection.execute(text("INSERT INTO missing_table VALUES (:value)"), {"value": secret})
            assert secret not in str(error.value)
        assert "SELECT" in caplog.text
        assert secret not in caplog.text
    finally:
        debug_engine.dispose()
