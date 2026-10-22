"""Bounded code generation and retries for automatically assigned codes."""
import random
import string
from collections.abc import Callable

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.crud.transactions import commit_or_conflict, is_unique_violation_for

MAX_ATTEMPTS = 20


def code_generation_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Không thể tạo mã tự động. Vui lòng thử lại hoặc nhập mã thủ công.",
    )


def generate_unique_code(db: Session, model, field: str, *, prefix: str = "", digits: int = 6) -> str:
    column = getattr(model, field)
    for _ in range(MAX_ATTEMPTS):
        code = prefix + "".join(random.choices(string.digits, k=digits))
        if db.query(model).filter(column == code).first() is None:
            return code
    raise code_generation_error()


def is_code_collision(error: HTTPException, model, field: str) -> bool:
    cause = error.__cause__
    if error.status_code != 409 or not isinstance(cause, IntegrityError):
        return False
    return is_unique_violation_for(cause, model, field)


def create_with_generated_code(
    db: Session, model, data: dict, field: str, generate: Callable[[Session], str],
):
    automatic = not data.get(field)
    for _ in range(MAX_ATTEMPTS):
        values = dict(data)
        if automatic:
            values[field] = generate(db)
        record = model(**values)
        db.add(record)
        try:
            commit_or_conflict(db)
        except HTTPException as error:
            # commit_or_conflict has already rolled back the failed insertion.
            if automatic and is_code_collision(error, model, field):
                continue
            raise
        db.refresh(record)
        return record
    raise code_generation_error()
