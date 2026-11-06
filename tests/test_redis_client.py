import runpy
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings


@pytest.mark.parametrize("override_environment", [False, True])
def test_redis_client_reads_dotenv_with_environment_precedence(
    tmp_path, monkeypatch, override_environment
):
    monkeypatch.delenv("REDIS_HOST", raising=False)
    monkeypatch.delenv("REDIS_PORT", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("REDIS_HOST=cache.internal\nREDIS_PORT=6380\n", encoding="utf-8")
    expected_host, expected_port = "cache.internal", 6380
    if override_environment:
        monkeypatch.setenv("REDIS_HOST", "cache.override")
        monkeypatch.setenv("REDIS_PORT", "6381")
        expected_host, expected_port = "cache.override", 6381

    config = Settings(_env_file=env_file)
    assert (config.REDIS_HOST, config.REDIS_PORT) == (expected_host, expected_port)
    monkeypatch.setattr("app.core.config.settings", config)

    # Constructing the client must not require a running Redis server.
    client_path = Path(__file__).resolve().parents[1] / "app" / "redis_client.py"
    client = runpy.run_path(str(client_path))["redis_client"]
    try:
        connection = client.connection_pool.connection_kwargs
        assert (connection["host"], connection["port"]) == (expected_host, expected_port)
    finally:
        client.close()


@pytest.mark.parametrize("port", ["0", "-1", "65536", "not-a-port"])
def test_invalid_redis_port_is_rejected(monkeypatch, port):
    monkeypatch.setenv("REDIS_PORT", port)
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None)
    assert any(item["loc"] == ("REDIS_PORT",) for item in error.value.errors())
