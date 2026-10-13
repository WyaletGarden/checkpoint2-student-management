from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from app.crud import crud_teacher
from app.schemas.teacher_schema import TeacherCreate, TeacherUpdate
from app.core.logger import get_logger

logger = get_logger(__name__)

class TeacherService:

    @staticmethod
    def get_all_teachers(db: Session, skip: int = 0, limit: int = 100):
        logger.info("Yêu cầu lấy danh sách giảng viên")
        return crud_teacher.get_teachers(db, skip=skip, limit=limit)

    @staticmethod
    def get_teacher_by_id(db: Session, teacher_id: int):
        logger.info(f"Yêu cầu lấy thông tin giảng viên ID: {teacher_id}")
        teacher = crud_teacher.get_teacher(db, teacher_id)
        if not teacher:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy giảng viên với ID {teacher_id}"
            )
        return teacher

    @staticmethod
    def create_new_teacher(db: Session, teacher_in: TeacherCreate):
        logger.info(f"Yêu cầu tạo mới giảng viên: {teacher_in.last_name} {teacher_in.first_name}")
        return crud_teacher.create_teacher(db=db, teacher=teacher_in)

    @staticmethod
    def update_existing_teacher(db: Session, teacher_id: int, teacher_in: TeacherUpdate):
        logger.info(f"Yêu cầu cập nhật giảng viên ID: {teacher_id}")
        updated = crud_teacher.update_teacher(db=db, teacher_id=teacher_id, teacher=teacher_in)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy giảng viên với ID {teacher_id} để cập nhật"
            )
        return updated

    @staticmethod
    def delete_existing_teacher(db: Session, teacher_id: int):
        logger.info(f"Yêu cầu xóa giảng viên ID: {teacher_id}")
        deleted = crud_teacher.delete_teacher(db=db, teacher_id=teacher_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy giảng viên với ID {teacher_id} để xóa"
            )
        return deleted