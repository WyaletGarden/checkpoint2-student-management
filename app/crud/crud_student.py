from sqlalchemy.orm import Session
from app.models.student import StudentModel
from app.schemas.student import StudentCreate, StudentUpdate

def get_student(db: Session, student_id: int):
    return db.query(StudentModel).filter(StudentModel.id == student_id).first()

def get_students(db: Session, class_id: str | None = None, skip: int = 0, limit: int = 100):
    query = db.query(StudentModel)
    if class_id:
        query = query.filter(StudentModel.class_id == class_id)
    return query.offset(skip).limit(limit).all()

def create_student(db: Session, student: StudentCreate):
    db_student = StudentModel(name=student.name, class_id=student.class_id, score=student.score)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def update_student(db: Session, student_id: int, student: StudentUpdate):
    db_student = get_student(db, student_id)
    if not db_student:
        return None
    
    # Lấy ra các dictionary chỉ gồm những field mà client thực sự truyền lên
    update_data = student.model_dump(exclude_unset=True)
    
    # Gán giá trị mới cho đúng các field đó, giữ nguyên các field cũ nếu không được truyền
    for key, value in update_data.items():
        setattr(db_student, key, value)
        
    db.commit()
    db.refresh(db_student)
    return db_student

def delete_student(db: Session, student_id: int):
    db_student = get_student(db, student_id)
    if not db_student:
        return None
    db.delete(db_student)
    db.commit()
    return db_student