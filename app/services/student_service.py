from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app.crud.crud_student import (
    get_student,
    get_students,
    create_student,
    update_student,
    delete_student,
)
from app.schemas.student import StudentCreate, StudentUpdate
from app.core.logger import get_logger

# Khởi tạo logger cho service
logger = get_logger(__name__)

class StudentService:
    @staticmethod
    def get_all_students(db: Session, class_id: Optional[str] = None, skip: int = 0, limit: int = 100):
        logger.info(f"Yêu cầu lấy danh sách học sinh (class_id={class_id}, skip={skip}, limit={limit})")
        return get_students(db, class_id=class_id, skip=skip, limit=limit)

    @staticmethod
    def get_student_by_id(db: Session, student_id: int):
        logger.info(f"Yêu cầu xem thông tin học sinh ID: {student_id}")
        student = get_student(db, student_id=student_id)
        if not student:
            logger.warning(f"Không tìm thấy học sinh với ID: {student_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Học sinh không tồn tại"
            )
        return student

    @staticmethod
    def create_new_student(db: Session, student_in: StudentCreate):
        logger.info(f"Yêu cầu tạo mới học sinh: {student_in.name} (Lớp: {student_in.class_id})")
        return create_student(db, student=student_in)

    @staticmethod
    def update_existing_student(db: Session, student_id: int, student_in: StudentUpdate):
        logger.info(f"Yêu cầu cập nhật thông tin học sinh ID: {student_id}")
        # Kiểm tra xem học sinh có tồn tại trước khi cập nhật
        student = get_student(db, student_id=student_id)
        if not student:
            logger.warning(f"Cập nhật thất bại - Không tìm thấy học sinh ID: {student_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Học sinh không tồn tại"
            )
        return update_student(db, student_id=student_id, student=student_in)

    @staticmethod
    def delete_existing_student(db: Session, student_id: int):
        logger.info(f"Yêu cầu xóa học sinh ID: {student_id}")
        student = get_student(db, student_id=student_id)
        if not student:
            logger.warning(f"Xóa thất bại - Không tìm thấy học sinh ID: {student_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Học sinh không tồn tại"
            )
        return delete_student(db, student_id=student_id)