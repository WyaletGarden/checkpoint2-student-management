"""Best-effort Redis cache for serialized student list pages."""

import hashlib
import json
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationError
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.logger import get_logger
from app.redis_client import redis_client
from app.schemas.student import StudentResponse, StudentSort

logger = get_logger(__name__)


class CachedStudentPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    students: list[StudentResponse]
    total: int = Field(ge=0, strict=True)


def read_student_list_cache(
    *, class_id: int | None, sort_by: StudentSort | None, skip: int, limit: int,
    q: str | None,
) -> tuple[str | None, CachedStudentPage | None]:
    if settings.STUDENTS_CACHE_TTL_SECONDS == 0:
        return None, None

    prefix = f"{settings.STUDENTS_CACHE_NAMESPACE}:students:list:v1"
    generation_key = f"{prefix}:generation"
    try:
        generation = redis_client.get(generation_key)
        if generation is None:
            candidate = uuid4().hex
            if redis_client.set(generation_key, candidate, nx=True):
                generation = candidate
            else:
                generation = redis_client.get(generation_key)
                if generation is None:
                    return None, None

        parameters = json.dumps(
            {"class_id": class_id, "sort_by": sort_by, "skip": skip,
             "limit": limit, "q": q},
            sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        )
        digest = hashlib.sha256(parameters.encode("utf-8")).hexdigest()
        key = f"{prefix}:{generation}:{digest}"
        payload = redis_client.get(key)
    except (RedisError, UnicodeDecodeError):
        logger.warning("Student list cache unavailable; reading from the database")
        return None, None

    if payload is not None:
        try:
            return key, CachedStudentPage.model_validate_json(payload)
        except ValidationError:
            logger.warning("Invalid student list cache entry; reading from the database")
    return key, None


def write_student_list_cache(key: str | None, students, total: int) -> None:
    if key is None or settings.STUDENTS_CACHE_TTL_SECONDS == 0:
        return

    page = CachedStudentPage(
        students=[StudentResponse.model_validate(student) for student in students],
        total=total,
    )
    try:
        redis_client.set(key, page.model_dump_json(), ex=settings.STUDENTS_CACHE_TTL_SECONDS)
    except RedisError:
        logger.warning("Could not store student list cache; returning database results")


def invalidate_student_list_cache() -> None:
    if settings.STUDENTS_CACHE_TTL_SECONDS == 0:
        return
    try:
        # In-flight reads retain their old generation, so they cannot refill
        # the active namespace with data queried before this mutation.
        generation_key = f"{settings.STUDENTS_CACHE_NAMESPACE}:students:list:v1:generation"
        redis_client.set(generation_key, uuid4().hex)
    except RedisError:
        logger.warning("Could not invalidate student list cache; entries will expire by TTL")
