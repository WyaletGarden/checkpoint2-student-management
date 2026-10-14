import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load các biến từ file .env
load_dotenv()

# Lấy DATABASE_URL từ .env
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

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