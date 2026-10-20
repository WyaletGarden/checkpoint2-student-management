from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload  # 1. Import joinedload từ sqlalchemy.orm
from app.core.database import get_db
from app.models.student import Student
from app.api.deps import get_current_user

router = APIRouter(prefix="/demo", tags=["Demo N+1 Query"], dependencies=[Depends(get_current_user)])

@router.get("/fixed-n-plus-1")
def get_students_fixed(db: Session = Depends(get_db)):
    # 2. Thêm .options(joinedload(Student.class_room)) vào câu query
    # Câu lệnh này sẽ tự động sinh ra cú pháp SQL JOIN bảng classes ngay lập tức.
    students = db.query(Student).options(joinedload(Student.class_room)).all()
    
    response_data = []
    
    # 3. Vòng lặp duyệt qua danh sách sinh viên
    for student in students:
        # Lúc này class_room đã được "nạp sẵn" từ đầu, vòng lặp chạy cực nhanh
        # và hoàn toàn KHÔNG phát sinh thêm bất kỳ câu lệnh SQL nào nữa!
        class_name = student.class_room.class_name if student.class_room else "Chưa phân lớp"
        
        response_data.append({
            "student_code": student.student_code,
            "full_name": f"{student.last_name} {student.first_name}",
            "class_name": class_name
        })
        
    return {
        "message": "Đã tối ưu thành công! Xử lý lỗi N+1 bằng joinedload.",
        "total_students": len(students),
        "data": response_data
    }
