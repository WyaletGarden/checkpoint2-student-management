"""Translate unique violations only; preserve other database errors."""
import sqlite3

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


def commit_or_conflict(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        original = exc.orig
        sqlstate = getattr(original, "sqlstate", None) or getattr(original, "pgcode", None)
        sqlite_code = getattr(original, "sqlite_errorcode", None)
        if sqlstate == "23505" or sqlite_code in {
            sqlite3.SQLITE_CONSTRAINT_UNIQUE, sqlite3.SQLITE_CONSTRAINT_PRIMARYKEY,
        }:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Mã hoặc email đã tồn tại. Vui lòng sử dụng giá trị khác.",
            ) from exc
        raise
