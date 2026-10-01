from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import get_db
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse
from app.services.student_service import StudentService

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("/", response_model=List[StudentResponse])
def get_students(
    class_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    return StudentService.get_all_students(db, class_id=class_id, skip=skip, limit=limit)

@router.get("/{id}", response_model=StudentResponse)
def get_student(id: int, db: Session = Depends(get_db)):
    return StudentService.get_student_by_id(db, student_id=id)

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    return StudentService.create_new_student(db=db, student_in=student)

@router.put("/{id}", response_model=StudentResponse)
def update_student(id: int, student: StudentUpdate, db: Session = Depends(get_db)):
    return StudentService.update_existing_student(db=db, student_id=id, student_in=student)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(id: int, db: Session = Depends(get_db)):
    StudentService.delete_existing_student(db=db, student_id=id)
    return None