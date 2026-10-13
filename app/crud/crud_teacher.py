import random
import string
from sqlalchemy.orm import Session
from app.models.teacher import Teacher
from app.schemas.teacher_schema import TeacherCreate, TeacherUpdate

def generate_unique_teacher_code(db: Session) -> str:
    while True:
        random_digits = "".join(random.choices(string.digits, k=6))
        code = f"GV{random_digits}"
        exists = db.query(Teacher).filter(Teacher.teacher_code == code).first()
        if not exists:
            return code

def get_teachers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Teacher).offset(skip).limit(limit).all()

def get_teacher(db: Session, teacher_id: int):
    return db.query(Teacher).filter(Teacher.id == teacher_id).first()

def create_teacher(db: Session, teacher: TeacherCreate):
    data = teacher.model_dump()
    if not data.get("teacher_code"):
        data["teacher_code"] = generate_unique_teacher_code(db)

    db_teacher = Teacher(**data)
    db.add(db_teacher)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher

def update_teacher(db: Session, teacher_id: int, teacher: TeacherUpdate):
    db_teacher = get_teacher(db, teacher_id)
    if not db_teacher:
        return None
    update_data = teacher.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_teacher, key, value)
    db.commit()
    db.refresh(db_teacher)
    return db_teacher

def delete_teacher(db: Session, teacher_id: int):
    db_teacher = get_teacher(db, teacher_id)
    if not db_teacher:
        return None
    db.delete(db_teacher)
    db.commit()
    return db_teacher