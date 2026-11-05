from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, selectinload  # 1. Import selectinload từ sqlalchemy.orm
from app.core.database import get_db
from app.models.student import Student
from app.api.deps import require_admin

router = APIRouter(prefix="/demo", tags=["Demo N+1 Query"], dependencies=[Depends(require_admin)])

@router.get("/fixed-n-plus-1")
def get_students_fixed(db: Session = Depends(get_db)):
    # 2. Tải sinh viên trước, sau đó tải các lớp liên quan theo nhóm bằng WHERE IN.
    # selectinload tránh truy vấn riêng cho từng sinh viên khi truy cập class_room.
    students = db.query(Student).options(selectinload(Student.class_room)).all()
    
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
        "message": "Đã tối ưu thành công! Xử lý lỗi N+1 bằng selectinload.",
        "total_students": len(students),
        "data": response_data
    }
