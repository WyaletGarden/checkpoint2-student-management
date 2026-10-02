from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Khởi tạo SQLite engine
engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- HÀM DEPENDENCY CUNG CẤP PHIÊN LÀM VIỆC DATABASE ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()