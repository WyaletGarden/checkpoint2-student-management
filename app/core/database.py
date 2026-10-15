from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Use the same settings as Alembic (including .env and environment overrides).
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Khởi tạo engine với echo=True để in toàn bộ câu lệnh SQL ra terminal
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
