from sqlalchemy.orm import Session
from app.models.student import StudentModel
from app.schemas.student import StudentCreate, StudentUpdate

def get_student(db: Session, student_id: int):
    return db.query(StudentModel).filter(StudentModel.id == student_id).first()

def get_students(db: Session, class_id: str | None = None, sort_by: str | None = None, skip: int = 0, limit: int = 100):
    query = db.query(StudentModel)
    
    # Lọc theo lớp nếu có
    if class_id:
        query = query.filter(StudentModel.class_id == class_id)
        
    # Sắp xếp dựa theo yêu cầu
    if sort_by == "first_name":
        query = query.order_by(StudentModel.first_name.asc())
    elif sort_by == "score_desc":
        query = query.order_by(StudentModel.score.desc())
    elif sort_by == "score_asc":
        query = query.order_by(StudentModel.score.asc())
    else:
        # Mặc định sắp xếp theo ID mới nhất
        query = query.order_by(StudentModel.id.desc())
        
    return query.offset(skip).limit(limit).all()

def get_distinct_classes(db: Session):
    return [row[0] for row in db.query(StudentModel.class_id).distinct().all() if row[0]]

def create_student(db: Session, student: StudentCreate):
    db_student = StudentModel(
        last_name=student.last_name,
        first_name=student.first_name,
        class_id=student.class_id,
        score=student.score
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student

def update_student(db: Session, student_id: int, student: StudentUpdate):
    db_student = get_student(db, student_id)
    if not db_student:
        return None
    
    update_data = student.model_dump(exclude_unset=True)
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