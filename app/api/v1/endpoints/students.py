from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import get_db
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse
from app.crud import crud_student

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("/", response_model=List[StudentResponse])
def get_students(class_id: Optional[str] = None, db: Session = Depends(get_db)):
    """1. Lấy danh sách học sinh (hỗ trợ lọc theo query param class_id)"""
    students = crud_student.get_students(db, class_id=class_id)
    return students

@router.get("/{id}", response_model=StudentResponse)
def get_student(id: int, db: Session = Depends(get_db)):
    """2. Lấy 1 học sinh theo ID, trả về 404 nếu không tồn tại"""
    db_student = crud_student.get_student(db, student_id=id)
    if not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Học sinh không tồn tại")
    return db_student

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    """3. Tạo mới học sinh với validate input (name không rỗng, score từ 0-10)"""
    return crud_student.create_student(db=db, student=student)

@router.put("/{id}", response_model=StudentResponse)
def update_student(id: int, student: StudentUpdate, db: Session = Depends(get_db)):
    """4. Cập nhật toàn bộ thông tin học sinh"""
    db_student = crud_student.update_student(db=db, student_id=id, student=student)
    if not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Học sinh không tồn tại")
    return db_student

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(id: int, db: Session = Depends(get_db)):
    """5. Xóa học sinh, trả về 204 khi thành công"""
    db_student = crud_student.delete_student(db=db, student_id=id)
    if not db_student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Học sinh không tồn tại")
    return None