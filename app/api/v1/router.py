from fastapi import APIRouter, Depends
from app.api.deps import get_current_user
from app.api.v1.endpoints import students, classes, teachers

api_router = APIRouter(dependencies=[Depends(get_current_user)])
api_router.include_router(students.router)
api_router.include_router(classes.router)
api_router.include_router(teachers.router)
