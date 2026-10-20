from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from app.crud import crud_class
from app.models.teacher import Teacher
from app.models.student import Student
from app.schemas.class_schema import ClassCreate, ClassUpdate
from app.core.logger import get_logger

logger = get_logger(__name__)

class ClassService:

    @staticmethod
    def get_all_classes(db: Session, skip: int = 0, limit: int = 100, q: str | None = None):
        logger.info("Yêu cầu lấy danh sách lớp học")
        return crud_class.get_classes(db, skip=skip, limit=limit, q=q)

    @staticmethod
    def get_class_by_id(db: Session, class_id: int):
        logger.info(f"Yêu cầu lấy thông tin lớp học ID: {class_id}")
        db_class = crud_class.get_class(db, class_id)
        if not db_class:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy lớp học với ID {class_id}"
            )
        return db_class

    @staticmethod
    def create_new_class(db: Session, class_in: ClassCreate):
        logger.info(f"Yêu cầu tạo mới lớp học: {class_in.class_name}")
        
        if class_in.teacher_id:
            teacher_exists = db.query(Teacher).filter(Teacher.id == class_in.teacher_id).first()
            if not teacher_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Giảng viên với ID {class_in.teacher_id} không tồn tại."
                )
                
        return crud_class.create_class(db=db, class_in=class_in)

    @staticmethod
    def update_existing_class(db: Session, class_id: int, class_in: ClassUpdate):
        logger.info(f"Yêu cầu cập nhật lớp học ID: {class_id}")
        
        if class_in.teacher_id is not None:
            teacher_exists = db.query(Teacher).filter(Teacher.id == class_in.teacher_id).first()
            if not teacher_exists:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Giảng viên với ID {class_in.teacher_id} không tồn tại."
                )
                
        updated = crud_class.update_class(db=db, class_id=class_id, class_in=class_in)
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy lớp học với ID {class_id} để cập nhật"
            )
        return updated

    @staticmethod
    def delete_existing_class(db: Session, class_id: int):
        logger.info(f"Yêu cầu xóa lớp học ID: {class_id}")
        ClassService.get_class_by_id(db, class_id)
        if db.query(Student.id).filter(Student.class_id == class_id).first() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Không thể xóa lớp đang có sinh viên. Vui lòng chuyển lớp hoặc xóa sinh viên trước."
            )
        deleted = crud_class.delete_class(db=db, class_id=class_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy lớp học với ID {class_id} để xóa"
            )
        return deleted
