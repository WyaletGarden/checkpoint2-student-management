from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.core import database
from app.crud import codes
from app.models.class_model import Class
from app.models.teacher import Teacher


@pytest.mark.parametrize("attribute", ["sqlstate", "pgcode"])
@pytest.mark.parametrize("constraint,expected", [
    ("ix_teachers_teacher_code", True), ("ix_teachers_email", False), (None, False),
])
def test_postgres_retry_identifies_only_code_constraint(attribute, constraint, expected):
    original = Exception("database diagnostic")
    setattr(original, attribute, "23505")
    original.diag = Mock(constraint_name=constraint)
    error = HTTPException(status_code=409)
    error.__cause__ = IntegrityError("INSERT", {}, original)
    assert codes.is_code_collision(error, Teacher, "teacher_code") is expected


def test_database_dependency_rolls_back_and_closes(monkeypatch):
    session = Mock()
    monkeypatch.setattr(database, "SessionLocal", lambda: session)
    dependency = database.get_db()
    assert next(dependency) is session
    with pytest.raises(ValueError):
        dependency.throw(ValueError("failure"))
    session.rollback.assert_called_once()
    session.close.assert_called_once()
    session.commit.assert_not_called()


def test_database_dependency_closes_without_committing(monkeypatch):
    session = Mock()
    monkeypatch.setattr(database, "SessionLocal", lambda: session)
    assert list(database.get_db()) == [session]
    session.close.assert_called_once()
    session.rollback.assert_not_called()
    session.commit.assert_not_called()


def test_generation_stops_when_candidates_are_taken(monkeypatch):
    session = Mock()
    session.query.return_value.filter.return_value.first.return_value = object()
    monkeypatch.setattr(codes, "MAX_ATTEMPTS", 3)
    with pytest.raises(HTTPException) as error:
        codes.generate_unique_code(session, Class, "class_code", digits=4)
    assert error.value.status_code == 503
    assert session.query.call_count == 3


def test_generated_collision_retries_real_insert(db, sample_class):
    generate = Mock(side_effect=[sample_class.class_code, "NEWCODE"])
    record = codes.create_with_generated_code(
        db, Class, {"class_name": "New class"}, "class_code", generate,
    )
    assert record.class_code == "NEWCODE"
    assert generate.call_count == 2
    assert db.query(Class).count() == 2


def test_generated_collisions_stop_after_limit(db, sample_class, monkeypatch):
    monkeypatch.setattr(codes, "MAX_ATTEMPTS", 3)
    generate = Mock(return_value=sample_class.class_code)
    with pytest.raises(HTTPException) as error:
        codes.create_with_generated_code(db, Class, {"class_name": "New"}, "class_code", generate)
    assert error.value.status_code == 503
    assert generate.call_count == 3
    assert db.query(Class).count() == 1


def test_explicit_duplicate_is_not_retried(db, sample_class):
    generate = Mock()
    with pytest.raises(HTTPException) as error:
        codes.create_with_generated_code(
            db, Class, {"class_name": "New", "class_code": sample_class.class_code},
            "class_code", generate,
        )
    assert error.value.status_code == 409
    generate.assert_not_called()


def test_duplicate_email_is_not_retried(db, sample_teacher):
    generate = Mock(return_value="GVNEW")
    with pytest.raises(HTTPException) as error:
        codes.create_with_generated_code(
            db, Teacher, {"last_name": "Test", "first_name": "User", "email": sample_teacher.email},
            "teacher_code", generate,
        )
    assert error.value.status_code == 409
    generate.assert_called_once()
