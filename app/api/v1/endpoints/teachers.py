from app.models.teacher import Teacher
from app.crud.search import search_query
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.deps import require_admin
from app.schemas.teacher_schema import TeacherCreate, TeacherUpdate, TeacherResponse
from app.services.teacher_service import TeacherService

router = APIRouter(prefix="/teachers", tags=["Teachers"])

@router.get("/", response_model=List[TeacherResponse])
def get_teachers(response: Response, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), q: str | None = Query(None, max_length=100), db: Session = Depends(get_db)):
    response.headers['X-Total-Count'] = str(search_query(db.query(Teacher), Teacher, q).count())
    return TeacherService.get_all_teachers(db, skip=skip, limit=limit, q=q)

@router.get("/{id}", response_model=TeacherResponse)
def get_teacher(id: int, db: Session = Depends(get_db)):
    return TeacherService.get_teacher_by_id(db, teacher_id=id)

@router.post("/", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin)])
def create_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    return TeacherService.create_new_teacher(db=db, teacher_in=teacher)

@router.put("/{id}", response_model=TeacherResponse, dependencies=[Depends(require_admin)])
def update_teacher(id: int, teacher: TeacherUpdate, db: Session = Depends(get_db)):
    return TeacherService.update_existing_teacher(db=db, teacher_id=id, teacher_in=teacher)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_admin)])
def delete_teacher(id: int, db: Session = Depends(get_db)):
    TeacherService.delete_existing_teacher(db=db, teacher_id=id)
    return None
