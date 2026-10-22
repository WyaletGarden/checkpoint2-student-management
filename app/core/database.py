from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Use the same settings as Alembic (including .env and environment overrides).
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# SQL logging is opt-in; bound parameter values remain hidden.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=settings.SQL_ECHO,
    hide_parameters=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
