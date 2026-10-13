import random
import string
from sqlalchemy.orm import Session, joinedload
from app.models.class_model import Class
from app.schemas.class_schema import ClassCreate, ClassUpdate

def generate_unique_class_code(db: Session) -> str:
    while True:
        code = "".join(random.choices(string.digits, k=4))
        exists = db.query(Class).filter(Class.class_code == code).first()
        if not exists:
            return code

def get_classes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Class).options(joinedload(Class.advisor)).offset(skip).limit(limit).all()

def get_class(db: Session, class_id: int):
    return db.query(Class).options(joinedload(Class.advisor)).filter(Class.id == class_id).first()

def create_class(db: Session, class_in: ClassCreate):
    data = class_in.model_dump()
    if not data.get("class_code"):
        data["class_code"] = generate_unique_class_code(db)

    db_class = Class(**data)
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    return get_class(db, db_class.id)

def update_class(db: Session, class_id: int, class_in: ClassUpdate):
    db_class = get_class(db, class_id)
    if not db_class:
        return None
    update_data = class_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_class, key, value)
    db.commit()
    db.refresh(db_class)
    return get_class(db, class_id)

def delete_class(db: Session, class_id: int):
    db_class = get_class(db, class_id)
    if not db_class:
        return None
    db.delete(db_class)
    db.commit()
    return db_class