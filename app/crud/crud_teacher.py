from app.crud.transactions import commit_or_conflict
from app.crud.search import search_query
from app.crud.codes import create_with_generated_code, generate_unique_code
from sqlalchemy.orm import Session
from app.models.teacher import Teacher
from app.schemas.teacher_schema import TeacherCreate, TeacherUpdate

def generate_unique_teacher_code(db: Session) -> str:
    return generate_unique_code(db, Teacher, "teacher_code", prefix="GV")


def get_teachers(db: Session, skip: int = 0, limit: int = 100, q: str | None = None):
    return search_query(db.query(Teacher), Teacher, q).order_by(Teacher.id.asc()).offset(skip).limit(limit).all()

def get_teacher(db: Session, teacher_id: int):
    return db.query(Teacher).filter(Teacher.id == teacher_id).first()

def create_teacher(db: Session, teacher: TeacherCreate):
    record = create_with_generated_code(
        db, Teacher, teacher.model_dump(), "teacher_code", generate_unique_teacher_code,
    )
    return record


def update_teacher(db: Session, teacher_id: int, teacher: TeacherUpdate):
    db_teacher = get_teacher(db, teacher_id)
    if not db_teacher:
        return None
    update_data = teacher.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_teacher, key, value)
    commit_or_conflict(db)
    db.refresh(db_teacher)
    return db_teacher

def delete_teacher(db: Session, teacher_id: int):
    db_teacher = get_teacher(db, teacher_id)
    if not db_teacher:
        return None
    db.delete(db_teacher)
    commit_or_conflict(db)
    return db_teacher
