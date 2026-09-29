from fastapi import FastAPI
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router
from app.models.student import StudentModel

# Tạo bảng trong CSDL (dùng cho SQLite/Dev)
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "Student Management API is running!"}