import logging
import sqlite3
from unittest.mock import Mock

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.api.v1.endpoints.auth import register
from app.crud.transactions import is_unique_violation_for
from app.main import global_exception_handler, logger
from app.models.user import User
from app.schemas.auth import Credentials


@pytest.mark.parametrize("attribute", ["sqlstate", "pgcode"])
@pytest.mark.parametrize("constraint,expected", [
    ("users_username_key", True), ("users_pkey", False), (None, False),
])
def test_postgres_username_constraint(attribute, constraint, expected):
    original = Exception("database diagnostic")
    setattr(original, attribute, "23505")
    original.diag = Mock(constraint_name=constraint)
    error = IntegrityError("INSERT", {}, original)
    assert is_unique_violation_for(error, User, "username") is expected


@pytest.mark.parametrize("code,message,conflict", [
    (sqlite3.SQLITE_CONSTRAINT_UNIQUE, "UNIQUE constraint failed: users.username", True),
    (sqlite3.SQLITE_CONSTRAINT_NOTNULL, "NOT NULL constraint failed: users.hashed_password", False),
    (sqlite3.SQLITE_CONSTRAINT_CHECK, "CHECK constraint failed: ck_users_role", False),
    (sqlite3.SQLITE_CONSTRAINT_FOREIGNKEY, "FOREIGN KEY constraint failed", False),
    (sqlite3.SQLITE_CONSTRAINT_UNIQUE, "UNIQUE constraint failed: users.other", False),
])
def test_registration_commit_error_classification(monkeypatch, code, message, conflict):
    # A stale pre-check simulates a concurrent registration winning the race.
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = None
    original = sqlite3.IntegrityError(message)
    original.sqlite_errorcode = code
    error = IntegrityError("INSERT", {}, original)
    db.commit.side_effect = error
    monkeypatch.setattr("app.api.v1.endpoints.auth.hash_password", lambda _: "test-hash")
    with pytest.raises(HTTPException if conflict else IntegrityError) as caught:
        register(Credentials(username="newuser", password="password123"), db)
    if conflict:
        assert caught.value.status_code == 409
        assert caught.value.detail == "Username already registered"
    else:
        assert caught.value is error
    db.rollback.assert_called_once()


def test_registration_collision_rolls_back_real_session(db, monkeypatch):
    db.add(User(username="taken", hashed_password="unused"))
    db.commit()
    # Force the pre-check to miss the existing record; commit must catch it.
    monkeypatch.setattr(db, "query", Mock())
    db.query.return_value.filter.return_value.first.return_value = None
    monkeypatch.setattr("app.api.v1.endpoints.auth.hash_password", lambda _: "test-hash")
    with pytest.raises(HTTPException) as caught:
        register(Credentials(username="taken", password="password123"), db)
    assert caught.value.status_code == 409
    db.add(User(username="available", hashed_password="unused"))
    db.commit()


def test_global_handler_logs_traceback_and_returns_generic_response():
    test_app = FastAPI()
    test_app.add_exception_handler(Exception, global_exception_handler)

    @test_app.post("/failure")
    def fail():
        raise RuntimeError("internal diagnostic")

    records = []

    class Capture(logging.Handler):
        def emit(self, record):
            records.append(record)

    handler = Capture()
    logger.addHandler(handler)
    try:
        with TestClient(test_app, raise_server_exceptions=False) as client:
            response = client.post(
                "/failure?token=private-query",
                headers={"Authorization": "Bearer private-header"},
                json={"password": "private-password"},
            )
        assert response.status_code == 500
        assert response.json()["error"] == "Internal Server Error"
        assert "internal diagnostic" not in response.text
        record = next(record for record in records if record.getMessage() == "Unhandled error: POST /failure")
        assert record.exc_info[0] is RuntimeError
        assert record.exc_info[2] is not None
        output = logging.Formatter().format(record)
        for secret in ("private-query", "private-header", "private-password"):
            assert secret not in output
    finally:
        logger.removeHandler(handler)
