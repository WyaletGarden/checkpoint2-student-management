import json

import pytest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.main import app


@pytest.fixture
def cors_client():
    middleware = next(item for item in app.user_middleware if item.cls is CORSMiddleware)
    options = {**middleware.kwargs, "allow_origins": ["https://students.example.com"]}
    with TestClient(CORSMiddleware(app, **options)) as client:
        yield client


def test_allowed_origin(cors_client):
    response = cors_client.get("/openapi.json", headers={"Origin": "https://students.example.com"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://students.example.com"
    assert "X-Total-Count" in response.headers["access-control-expose-headers"]
    assert "access-control-allow-credentials" not in response.headers


@pytest.mark.parametrize("origin", ["https://evil.example.com", "http://students.example.com", "https://students.example.com:8443", "null"])
def test_disallowed_origin(cors_client, origin):
    response = cors_client.get("/openapi.json", headers={"Origin": origin})
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE"])
def test_preflight(cors_client, method):
    response = cors_client.options("/api/v1/students/", headers={
        "Origin": "https://students.example.com",
        "Access-Control-Request-Method": method,
        "Access-Control-Request-Headers": "authorization,content-type",
    })
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://students.example.com"


@pytest.mark.parametrize("origin,method,header", [
    ("https://evil.example.com", "GET", "authorization"),
    ("https://students.example.com", "PATCH", "authorization"),
    ("https://students.example.com", "GET", "X-Unapproved"),
])
def test_rejected_preflight(cors_client, origin, method, header):
    response = cors_client.options("/api/v1/students/", headers={
        "Origin": origin, "Access-Control-Request-Method": method,
        "Access-Control-Request-Headers": header,
    })
    assert response.status_code == 400


def test_without_origin(cors_client):
    response = cors_client.get("/openapi.json")
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize("origin", ["*", "https://*.example.com", "null", "ftp://example.com", "https://example.com/path", "https://example.com/", "https://user:pass@example.com", "https://example.com?x=1", "https://example.com#part", "example.com"])
def test_invalid_configuration(origin):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, CORS_ORIGINS=[origin])


def test_environment_configuration(monkeypatch):
    origins = ["https://students.example.com", "http://localhost:5173"]
    monkeypatch.setenv("CORS_ORIGINS", json.dumps(origins))
    assert Settings(_env_file=None).CORS_ORIGINS == origins


def test_default_configuration(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    assert Settings(_env_file=None).CORS_ORIGINS == []
    middleware = next(item for item in app.user_middleware if item.cls is CORSMiddleware)
    assert middleware.kwargs["allow_origins"] == settings.CORS_ORIGINS
