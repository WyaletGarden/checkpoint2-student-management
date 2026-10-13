from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.teacher_schema import TeacherCreate, TeacherUpdate, TeacherResponse
from app.services.teacher_service import TeacherService

router = APIRouter(prefix="/teachers", tags=["Teachers"])

@router.get("/", response_model=List[TeacherResponse])
def get_teachers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return TeacherService.get_all_teachers(db, skip=skip, limit=limit)

@router.get("/{id}", response_model=TeacherResponse)
def get_teacher(id: int, db: Session = Depends(get_db)):
    return TeacherService.get_teacher_by_id(db, teacher_id=id)

@router.post("/", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
def create_teacher(teacher: TeacherCreate, db: Session = Depends(get_db)):
    return TeacherService.create_new_teacher(db=db, teacher_in=teacher)

@router.put("/{id}", response_model=TeacherResponse)
def update_teacher(id: int, teacher: TeacherUpdate, db: Session = Depends(get_db)):
    return TeacherService.update_existing_teacher(db=db, teacher_id=id, teacher_in=teacher)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_teacher(id: int, db: Session = Depends(get_db)):
    TeacherService.delete_existing_teacher(db=db, teacher_id=id)
    return None