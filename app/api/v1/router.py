from fastapi import APIRouter
from app.api.v1.endpoints import students, classes, teachers

api_router = APIRouter()
api_router.include_router(students.router)
api_router.include_router(classes.router)
api_router.include_router(teachers.router)