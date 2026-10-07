from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.crud.crud_student import (
    get_students,
    get_student,
    create_student,
    update_student,
    delete_student,
    get_distinct_classes
)
from app.schemas.student import StudentCreate, StudentUpdate
from app.core.logger import get_logger

logger = get_logger(__name__)

class StudentService:

    @staticmethod
    def get_all_students(db: Session, class_id: str | None = None, sort_by: str | None = None, skip: int = 0, limit: int = 100):
        logger.info(f"Yêu cầu lấy danh sách học sinh (class_id={class_id}, sort_by={sort_by}, skip={skip}, limit={limit})")
        return get_students(db, class_id=class_id, sort_by=sort_by, skip=skip, limit=limit)

    @staticmethod
    def get_all_classes(db: Session):
        logger.info("Yêu cầu lấy danh sách tất cả các mã lớp học")
        return get_distinct_classes(db)

    @staticmethod
    def get_student_by_id(db: Session, student_id: int):
        logger.info(f"Yêu cầu lấy thông tin học sinh ID: {student_id}")
        student = get_student(db, student_id)
        
        # KIỂM TRA: Nếu không tìm thấy học sinh, chủ động văng lỗi 404
        if not student:
            logger.warning(f"Không tìm thấy học sinh với ID: {student_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy học sinh với ID {student_id}"
            )
            
        return student

    @staticmethod
    def create_new_student(db: Session, student_in: StudentCreate):
        logger.info(f"Yêu cầu tạo mới học sinh: {student_in.last_name} {student_in.first_name}")
        return create_student(db=db, student=student_in)

    @staticmethod
    def update_existing_student(db: Session, student_id: int, student_in: StudentUpdate):
        logger.info(f"Yêu cầu cập nhật học sinh ID: {student_id}")
        updated = update_student(db=db, student_id=student_id, student=student_in)
        if not updated:
            logger.warning(f"Không thể cập nhật, không tìm thấy học sinh ID: {student_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy học sinh với ID {student_id} để cập nhật"
            )
        return updated

    @staticmethod
    def delete_existing_student(db: Session, student_id: int):
        logger.info(f"Yêu cầu xóa học sinh ID: {student_id}")
        deleted = delete_student(db=db, student_id=student_id)
        if not deleted:
            logger.warning(f"Không thể xóa, không tìm thấy học sinh ID: {student_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy học sinh với ID {student_id} để xóa"
            )
        return deleted