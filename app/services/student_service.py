from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from app.crud import crud_student
from app.models.class_model import Class
from app.schemas.student import StudentCreate, StudentUpdate
from app.core.logger import get_logger

logger = get_logger(__name__)

class StudentService:

    @staticmethod
    def get_all_students(db: Session, class_id: Optional[int] = None, sort_by: Optional[str] = None, skip: int = 0, limit: int = 100, q: str | None = None):
        logger.info(f"Yêu cầu lấy danh sách học sinh (class_id={class_id}, sort_by={sort_by})")
        return crud_student.get_students(db, class_id=class_id, sort_by=sort_by, skip=skip, limit=limit, q=q)

    @staticmethod
    def get_student_by_id(db: Session, student_id: int):
        logger.info(f"Yêu cầu lấy thông tin học sinh ID: {student_id}")
        student = crud_student.get_student(db, student_id)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy học sinh với ID {student_id}"
            )
        return student

    @staticmethod
    def create_new_student(db: Session, student_in: StudentCreate):
        logger.info(f"Yêu cầu tạo mới học sinh: {student_in.last_name} {student_in.first_name}")
        
        class_exists = db.query(Class).filter(Class.id == student_in.class_id).first()
        if not class_exists:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Lớp học với ID {student_in.class_id} không tồn tại."
            )
            
        return crud_student.create_student(db=db, student=student_in)

    @staticmethod
    def update_existing_student(db: Session, student_id: int, student_in: StudentUpdate):
        logger.info(f"Yêu cầu cập nhật học sinh ID: {student_id}")
        
        if student_in.class_id is not None:
            class_exists = db.query(Class).filter(Class.id == student_in.class_id).first()
            if not class_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Lớp học với ID {student_in.class_id} không tồn tại."
                )
                
        updated = crud_student.update_student(db=db, student_id=student_id, student=student_in)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy học sinh với ID {student_id} để cập nhật"
            )
        return updated

    @staticmethod
    def delete_existing_student(db: Session, student_id: int):
        logger.info(f"Yêu cầu xóa học sinh ID: {student_id}")
        deleted = crud_student.delete_student(db=db, student_id=student_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy học sinh với ID {student_id} để xóa"
            )
        return deleted
