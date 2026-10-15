from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.crud.transactions import commit_or_conflict


@pytest.mark.parametrize("attribute", ["sqlstate", "pgcode"])
def test_postgres_unique_violation_returns_conflict_and_rolls_back(attribute):
    db = Mock()
    original = Exception("private database diagnostic")
    setattr(original, attribute, "23505")
    db.commit.side_effect = IntegrityError("INSERT", {}, original)
    with pytest.raises(HTTPException) as error:
        commit_or_conflict(db)
    assert error.value.status_code == 409
    assert "private" not in error.value.detail
    db.rollback.assert_called_once_with()


@pytest.mark.parametrize("sqlstate", ["23502", "23503", "23514"])
def test_other_integrity_errors_are_not_reported_as_duplicates(sqlstate):
    db = Mock()
    original = Exception("other constraint")
    original.sqlstate = sqlstate
    error = IntegrityError("INSERT", {}, original)
    db.commit.side_effect = error
    with pytest.raises(IntegrityError) as raised:
        commit_or_conflict(db)
    assert raised.value is error
    db.rollback.assert_called_once_with()
