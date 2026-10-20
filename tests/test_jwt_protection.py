from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.core.config import settings
from app.models.user import User


@pytest.mark.parametrize("resource", ["students", "classes", "teachers"])
@pytest.mark.parametrize("method,suffix", [
    ("GET", "/"), ("GET", "/1"), ("POST", "/"),
    ("PUT", "/1"), ("DELETE", "/1"),
])
def test_crud_requires_login(public_client, resource, method, suffix):
    response = public_client.request(method, f"/api/v1/{resource}{suffix}")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("authorization", [None, "Basic abc", "Bearer", "Bearer not-a-jwt"])
def test_invalid_authorization_header(public_client, authorization):
    headers = {} if authorization is None else {"Authorization": authorization}
    response = public_client.get("/demo/fixed-n-plus-1", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.fixture
def token_user(db):
    user = User(username="token-user", hashed_password="unused")
    db.add(user)
    db.commit()
    return user


@pytest.mark.parametrize("case", [
    "expired", "wrong-key", "wrong-algorithm", "missing-exp", "missing-iat",
    "missing-sub", "invalid-sub", "huge-sub", "numeric-sub", "future-iat",
    "unsigned", "deleted-user",
])
def test_invalid_jwt_rejected(public_client, db, token_user, case):
    now = datetime.now(timezone.utc)
    payload = {"sub": str(token_user.id), "iat": now, "exp": now + timedelta(minutes=5)}
    key = settings.JWT_SECRET_KEY.get_secret_value()
    algorithm = "HS256"
    if case == "expired":
        payload.update(iat=now - timedelta(minutes=10), exp=now - timedelta(minutes=5))
    elif case == "wrong-key":
        key = "different-signing-secret" * 3
    elif case == "wrong-algorithm":
        algorithm = "HS512"
    elif case.startswith("missing-"):
        del payload[case.removeprefix("missing-")]
    elif case == "invalid-sub":
        payload["sub"] = "not-an-id"
    elif case == "huge-sub":
        payload["sub"] = "9" * 30
    elif case == "numeric-sub":
        payload["sub"] = token_user.id
    elif case == "future-iat":
        payload["iat"] = now + timedelta(minutes=1)
    elif case == "unsigned":
        algorithm, key = "none", ""
    elif case == "deleted-user":
        db.delete(token_user)
        db.commit()
    token = jwt.encode(payload, key, algorithm=algorithm)
    response = public_client.get("/api/v1/students/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_real_login_token_accesses_protected_routes(public_client):
    credentials = {"username": "student01", "password": "StrongPassword123!"}
    assert public_client.post("/register", json=credentials).status_code == 201
    response = public_client.post("/login", json=credentials)
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    for path in ["/api/v1/students/", "/api/v1/classes/", "/api/v1/teachers/", "/demo/fixed-n-plus-1"]:
        assert public_client.get(path, headers=headers).status_code == 200


def test_openapi_declares_bearer_auth(public_client):
    schema = public_client.get("/openapi.json").json()
    assert schema["paths"]["/api/v1/students/"]["get"]["security"] == [{"HTTPBearer": []}]
    for path in ["/register", "/login"]:
        assert not schema["paths"][path]["post"].get("security")
