from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import Credentials, TokenResponse, UserResponse

router = APIRouter(tags=["Authentication"])
# Use a real bcrypt hash for missing users as well to avoid a fast username probe.
_DUMMY_HASH = hash_password("dummy-password-for-timing")


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(credentials: Credentials, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == credentials.username).first():
        raise HTTPException(status_code=409, detail="Username already registered")
    user = User(username=credentials.username,
                hashed_password=hash_password(credentials.password.get_secret_value()))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Username already registered") from None
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(credentials: Credentials, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == credentials.username).first()
    valid = verify_password(credentials.password.get_secret_value(),
                            user.hashed_password if user else _DUMMY_HASH)
    if not valid or user is None:
        raise HTTPException(status_code=401, detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    return TokenResponse(access_token=create_access_token(user.id))
