from app.models.class_model import Class
from app.crud.search import search_query
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.api.deps import require_admin
from app.schemas.class_schema import ClassCreate, ClassUpdate, ClassResponse
from app.services.class_service import ClassService

router = APIRouter(prefix="/classes", tags=["Classes"])

@router.get("/", response_model=List[ClassResponse])
def get_classes(response: Response, skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=100), q: str | None = Query(None, max_length=100), db: Session = Depends(get_db)):
    response.headers['X-Total-Count'] = str(search_query(db.query(Class), Class, q).count())
    return ClassService.get_all_classes(db, skip=skip, limit=limit, q=q)

@router.get("/{id}", response_model=ClassResponse)
def get_class(id: int, db: Session = Depends(get_db)):
    return ClassService.get_class_by_id(db, class_id=id)

@router.post("/", response_model=ClassResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin)])
def create_class(class_in: ClassCreate, db: Session = Depends(get_db)):
    return ClassService.create_new_class(db=db, class_in=class_in)

@router.put("/{id}", response_model=ClassResponse, dependencies=[Depends(require_admin)])
def update_class(id: int, class_in: ClassUpdate, db: Session = Depends(get_db)):
    return ClassService.update_existing_class(db=db, class_id=id, class_in=class_in)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_admin)])
def delete_class(id: int, db: Session = Depends(get_db)):
    ClassService.delete_existing_class(db=db, class_id=id)
    return None
