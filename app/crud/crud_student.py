from app.crud.transactions import commit_or_conflict
from app.crud.search import search_query
from app.crud.codes import create_with_generated_code, generate_unique_code
from datetime import datetime
from sqlalchemy.orm import Query, Session, joinedload
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate, StudentSort

def generate_unique_student_code(db: Session) -> str:
    return generate_unique_code(db, Student, "student_code", prefix=datetime.now().strftime("%y"))


def build_student_query(
    db: Session, class_id: int | None = None, q: str | None = None
) -> Query[Student]:
    query = search_query(db.query(Student), Student, q)
    if class_id is not None:
        query = query.filter(Student.class_id == class_id)
    return query


def get_students(
    db: Session,
    class_id: int | None = None,
    sort_by: StudentSort | None = None,
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,
) -> tuple[list[Student], int]:
    query = build_student_query(db, class_id=class_id, q=q)
    total = query.count()
    query = query.options(joinedload(Student.class_room))

    if sort_by == "score_asc":
        query = query.order_by(Student.score.asc())
    elif sort_by == "score_desc":
        query = query.order_by(Student.score.desc())
    elif sort_by == "first_name":
        query = query.order_by(Student.first_name.asc())
    elif sort_by == "last_name":
        query = query.order_by(Student.last_name.asc())
        
    students = query.order_by(Student.id.asc()).offset(skip).limit(limit).all()
    return students, total

def get_student(db: Session, student_id: int):
    return db.query(Student).options(joinedload(Student.class_room)).filter(Student.id == student_id).first()

def create_student(db: Session, student: StudentCreate):
    record = create_with_generated_code(
        db, Student, student.model_dump(), "student_code", generate_unique_student_code,
    )
    return get_student(db, record.id)


def update_student(db: Session, student_id: int, student: StudentUpdate):
    db_student = get_student(db, student_id)
    if not db_student:
        return None
    update_data = student.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_student, key, value)
    commit_or_conflict(db)
    db.refresh(db_student)
    return get_student(db, student_id)

def delete_student(db: Session, student_id: int):
    db_student = get_student(db, student_id)
    if not db_student:
        return None
    db.delete(db_student)
    commit_or_conflict(db)
    return db_student
