"""Translate unique violations only; preserve other database errors."""
import sqlite3

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Session


def is_unique_violation(exc: IntegrityError) -> bool:
    original = exc.orig
    sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
    return sqlstate == "23505" or getattr(original, "sqlite_errorcode", None) in {
        sqlite3.SQLITE_CONSTRAINT_UNIQUE, sqlite3.SQLITE_CONSTRAINT_PRIMARYKEY,
    }


def is_unique_violation_for(exc: IntegrityError, model, field: str) -> bool:
    """Identify a single-column unique violation, failing closed if unknown."""
    if not is_unique_violation(exc):
        return False
    original = exc.orig
    table = model.__table__
    if getattr(original, "sqlite_errorcode", None) == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
        return str(original) == f"UNIQUE constraint failed: {table.name}.{field}"
    sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
    if sqlstate == "23505":
        constraint_name = getattr(getattr(original, "diag", None), "constraint_name", None)
        names = {index.name for index in table.indexes
                 if index.unique and [column.name for column in index.columns] == [field]}
        for constraint in table.constraints:
            if isinstance(constraint, UniqueConstraint) and [column.name for column in constraint.columns] == [field]:
                # PostgreSQL assigns this name to unnamed UNIQUE constraints.
                names.add(constraint.name or f"{table.name}_{field}_key")
        return constraint_name is not None and constraint_name in names
    return False


def commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if is_unique_violation(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Mã hoặc email đã tồn tại. Vui lòng sử dụng giá trị khác.",
            ) from exc
        raise
