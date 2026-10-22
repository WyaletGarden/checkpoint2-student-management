from app.crud.transactions import commit_or_conflict
from app.crud.search import search_query
from app.crud.codes import create_with_generated_code, generate_unique_code
from sqlalchemy.orm import Session, joinedload
from app.models.class_model import Class
from app.schemas.class_schema import ClassCreate, ClassUpdate

def generate_unique_class_code(db: Session) -> str:
    return generate_unique_code(db, Class, "class_code", digits=4)


def get_classes(db: Session, skip: int = 0, limit: int = 100, q: str | None = None):
    return search_query(db.query(Class).options(joinedload(Class.advisor)), Class, q).order_by(Class.id.asc()).offset(skip).limit(limit).all()

def get_class(db: Session, class_id: int):
    return db.query(Class).options(joinedload(Class.advisor)).filter(Class.id == class_id).first()

def create_class(db: Session, class_in: ClassCreate):
    record = create_with_generated_code(
        db, Class, class_in.model_dump(), "class_code", generate_unique_class_code,
    )
    return get_class(db, record.id)


def update_class(db: Session, class_id: int, class_in: ClassUpdate):
    db_class = get_class(db, class_id)
    if not db_class:
        return None
    update_data = class_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_class, key, value)
    commit_or_conflict(db)
    db.refresh(db_class)
    return get_class(db, class_id)

def delete_class(db: Session, class_id: int):
    db_class = get_class(db, class_id)
    if not db_class:
        return None
    db.delete(db_class)
    commit_or_conflict(db)
    return db_class
