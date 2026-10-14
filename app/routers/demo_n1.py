from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.student import Student

router = APIRouter(prefix="/demo", tags=["Demo N+1 Query"])

@router.get("/n-plus-1")
def get_students_with_n_plus_1(db: Session = Depends(get_db)):
    # 1. Truy vấn lấy toàn bộ danh sách sinh viên (Câu lệnh SELECT đầu tiên)
    students = db.query(Student).all()
    
    response_data = []
    
    # 2. Vòng lặp qua từng sinh viên
    for student in students:
        # 🛑 GÂY LỖI N+1: Truy cập student.class_room.class_name làm SQLAlchemy 
        # phải bắn thêm 1 câu lệnh SELECT riêng lẻ cho mỗi sinh viên.
        class_name = student.class_room.class_name if student.class_room else "Chưa phân lớp"
        
        response_data.append({
            "student_code": student.student_code,
            "full_name": f"{student.last_name} {student.first_name}",
            "class_name": class_name
        })
        
    return {
        "message": "Đã thực thi API gây lỗi N+1 Query!",
        "total_students": len(students),
        "data": response_data
    }