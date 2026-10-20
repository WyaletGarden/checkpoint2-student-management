from app.core.database import SessionLocal
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
import jwt

from app.core.config import settings
from app.core.database import get_db as get_auth_db
from app.models.user import User


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_auth_db),
) -> User:
    """Validate a signed, unexpired access token and resolve its active user."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithms=["HS256"],
            options={"require": ["sub", "iat", "exp"]},
        )
        subject = payload["sub"]
        # Reject malformed or out-of-range IDs before querying the database.
        if not isinstance(subject, str) or not subject.isascii() or not subject.isdecimal():
            raise unauthorized
        if len(subject) > 19 or not 0 < int(subject) <= 2**63 - 1:
            raise unauthorized
    except jwt.InvalidTokenError:
        raise unauthorized from None
    user = db.get(User, int(subject))
    if user is None:
        raise unauthorized
    return user

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
