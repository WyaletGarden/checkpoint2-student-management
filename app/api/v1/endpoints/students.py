from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Optional, Literal

from app.core.database import get_db
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse
from app.services.student_service import StudentService

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("/", response_model=List[StudentResponse])
def get_students(
    class_id: Optional[str] = None,
    # Sử dụng Literal để giới hạn các giá trị hợp lệ. 
    # Nếu truyền sai (ví dụ: sort_by=xxx), FastAPI sẽ tự động từ chối và trả về HTTP 422.
    sort_by: Optional[Literal["score", "score_asc", "score_desc", "first_name", "last_name", "id", "id_asc", "id_desc"]] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    return StudentService.get_all_students(db, class_id=class_id, sort_by=sort_by, skip=skip, limit=limit)

@router.get("/classes", response_model=List[str])
def get_classes(db: Session = Depends(get_db)):
    return StudentService.get_all_classes(db)

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