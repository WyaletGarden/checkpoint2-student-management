import random
import string
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate
from typing import Optional

def generate_unique_student_code(db: Session) -> str:
    year_prefix = datetime.now().strftime("%y")
    while True:
        random_digits = "".join(random.choices(string.digits, k=6))
        code = f"{year_prefix}{random_digits}"
        exists = db.query(Student).filter(Student.student_code == code).first()
        if not exists:
            return code

def get_students(db: Session, class_id: Optional[int] = None, sort_by: Optional[str] = None, skip: int = 0, limit: int = 100):
    query = db.query(Student).options(joinedload(Student.class_room))
    
    if class_id is not None:
        query = query.filter(Student.class_id == class_id)
        
    if sort_by == "score_asc":
        query = query.order_by(Student.score.asc())
    elif sort_by == "score_desc":
        query = query.order_by(Student.score.desc())
    elif sort_by == "first_name":
        query = query.order_by(Student.first_name.asc())
    elif sort_by == "last_name":
        query = query.order_by(Student.last_name.asc())
        
    return query.offset(skip).limit(limit).all()

def get_student(db: Session, student_id: int):
    return db.query(Student).options(joinedload(Student.class_room)).filter(Student.id == student_id).first()

def create_student(db: Session, student: StudentCreate):
    data = student.model_dump()
    if not data.get("student_code"):
        data["student_code"] = generate_unique_student_code(db)
    
    db_student = Student(**data)
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return get_student(db, db_student.id)

def update_student(db: Session, student_id: int, student: StudentUpdate):
    db_student = get_student(db, student_id)
    if not db_student:
        return None
    update_data = student.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_student, key, value)
    db.commit()
    db.refresh(db_student)
    return get_student(db, student_id)

def delete_student(db: Session, student_id: int):
    db_student = get_student(db, student_id)
    if not db_student:
        return None
    db.delete(db_student)
    db.commit()
    return db_student