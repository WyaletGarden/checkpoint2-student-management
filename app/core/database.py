from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Khởi tạo engine kết nối CSDL (dùng SQLite)
engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False}
)

# Khởi tạo SessionLocal dùng cho các dependency lấy session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Khởi tạo Base cho các Model ORM kế thừa
Base = declarative_base()