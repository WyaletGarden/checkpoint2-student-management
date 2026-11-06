"""Run inside the app container against its disposable smoke-test account."""

import json
import secrets
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from uuid import uuid4

from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.models.user import User
from app.redis_client import redis_client
from app.services.student_cache import read_student_list_cache


def request(method, path, payload=None, token=None):
    headers = {}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(f"http://127.0.0.1:8000{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=10) as response:
            return response.status, response.headers, response.read()
    except HTTPError as error:
        raise AssertionError(f"{method} {path} returned HTTP {error.code}") from None


def main():
    user_id = None
    cache_key = None
    username = f"compose_smoke_{uuid4().hex}"
    credentials = {"username": username, "password": secrets.token_urlsafe(24)}
    try:
        for path in ("/", "/docs", "/openapi.json"):
            assert request("GET", path)[0] == 200
        assert engine.dialect.name == "postgresql", "Compose must use PostgreSQL"
        with engine.connect() as connection:
            assert connection.execute(text("SELECT 1")).scalar_one() == 1
        assert redis_client.ping(), "Redis must be available"
        assert settings.STUDENTS_CACHE_TTL_SECONDS > 0, "Enable cache for the smoke test"

        status, _, body = request("POST", "/register", credentials)
        assert status == 201
        user_id = json.loads(body)["id"]
        _, _, body = request("POST", "/login", credentials)
        token = json.loads(body)["access_token"]

        # Only this unique query's cache entry is modified; user data is untouched.
        query = f"compose-smoke-{uuid4().hex}"
        parameters = {"class_id": None, "sort_by": None, "skip": 0, "limit": 1, "q": query}
        cache_key, _ = read_student_list_cache(**parameters)
        assert cache_key is not None, "Redis cache lookup failed"
        path = "/api/v1/students/?" + urlencode({"q": query, "limit": 1})
        _, headers, body = request("GET", path, token=token)
        assert json.loads(body) == [] and headers["X-Total-Count"] == "0"
        cached = json.loads(redis_client.get(cache_key))
        assert cached == {"students": [], "total": 0}
        assert 0 < redis_client.ttl(cache_key) <= settings.STUDENTS_CACHE_TTL_SECONDS

        # A distinctive total proves the next response is served from Redis.
        cached["total"] = 7
        redis_client.set(cache_key, json.dumps(cached), ex=60)
        _, headers, body = request("GET", path, token=token)
        assert json.loads(body) == [] and headers["X-Total-Count"] == "7", "Expected cache hit"

        redis_client.expire(cache_key, 1)
        time.sleep(1.2)
        assert redis_client.get(cache_key) is None, "Redis TTL did not expire"
        _, headers, body = request("GET", path, token=token)
        assert json.loads(body) == [] and headers["X-Total-Count"] == "0"
        assert json.loads(redis_client.get(cache_key))["total"] == 0
        print("Compose smoke passed: frontend, Swagger, PostgreSQL, auth, API, Redis hit and TTL.")
    finally:
        if cache_key is not None:
            redis_client.delete(cache_key)
        if user_id is not None:
            with SessionLocal() as db:
                db.query(User).filter(User.id == user_id, User.username == username).delete()
                db.commit()


if __name__ == "__main__":
    main()
