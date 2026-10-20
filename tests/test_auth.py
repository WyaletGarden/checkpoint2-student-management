import bcrypt
import jwt
import pytest

from app.core.config import settings
from app.models.user import User


CREDENTIALS = {"username": "testuser", "password": "StrongPassword123!"}


@pytest.fixture
def client(public_client):
    return public_client


def test_register_stores_only_bcrypt_hash(client, db):
    response = client.post("/register", json=CREDENTIALS)
    assert response.status_code == 201
    user = db.query(User).one()
    assert response.json() == {"id": user.id, "username": "testuser"}
    assert user.hashed_password != CREDENTIALS["password"]
    assert bcrypt.checkpw(CREDENTIALS["password"].encode(), user.hashed_password.encode())


def test_duplicate_username(client, db):
    assert client.post("/register", json=CREDENTIALS).status_code == 201
    assert client.post("/register", json=CREDENTIALS).status_code == 409
    assert db.query(User).count() == 1


def test_login_returns_signed_expiring_jwt(client):
    user = client.post("/register", json=CREDENTIALS).json()
    response = client.post("/login", json=CREDENTIALS)
    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    claims = jwt.decode(response.json()["access_token"],
                        settings.JWT_SECRET_KEY.get_secret_value(), algorithms=["HS256"])
    assert claims["sub"] == str(user["id"])
    assert claims["exp"] - claims["iat"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(response.json()["access_token"], "incorrect-key" * 4, algorithms=["HS256"])


def test_invalid_login(client):
    client.post("/register", json=CREDENTIALS)
    for credentials in [dict(CREDENTIALS, password="WrongPassword!"),
                        dict(CREDENTIALS, username="unknown")]:
        response = client.post("/login", json=credentials)
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
        assert response.json() == {"detail": "Incorrect username or password"}


@pytest.mark.parametrize("password", ["short", "x" * 73, "é" * 37])
def test_password_limits(client, db, password):
    for path in ["/register", "/login"]:
        assert client.post(path, json=dict(CREDENTIALS, password=password)).status_code == 422
    assert db.query(User).count() == 0


def test_passwords_have_unique_salts(client, db):
    client.post("/register", json=CREDENTIALS)
    client.post("/register", json=dict(CREDENTIALS, username="anotheruser"))
    users = db.query(User).all()
    assert users[0].hashed_password != users[1].hashed_password
