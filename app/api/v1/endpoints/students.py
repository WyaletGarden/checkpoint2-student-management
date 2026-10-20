from app.models.student import Student
from app.crud.search import search_query
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session
from typing import List, Optional, Literal

from app.core.database import get_db
from app.api.deps import require_admin
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse
from app.services.student_service import StudentService

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("/", response_model=List[StudentResponse])
def get_students(
    response: Response,
    class_id: Optional[int] = None,
    sort_by: Optional[Literal["score_asc", "score_desc", "first_name", "last_name"]] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    q: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db)
):
    count_query = search_query(db.query(Student), Student, q)
    if class_id is not None:
        count_query = count_query.filter(Student.class_id == class_id)
    response.headers['X-Total-Count'] = str(count_query.count())
    return StudentService.get_all_students(db, class_id=class_id, sort_by=sort_by, skip=skip, limit=limit, q=q)

@router.get("/{id}", response_model=StudentResponse)
def get_student(id: int, db: Session = Depends(get_db)):
    return StudentService.get_student_by_id(db, student_id=id)

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin)])
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    return StudentService.create_new_student(db=db, student_in=student)

@router.put("/{id}", response_model=StudentResponse, dependencies=[Depends(require_admin)])
def update_student(id: int, student: StudentUpdate, db: Session = Depends(get_db)):
    return StudentService.update_existing_student(db=db, student_id=id, student_in=student)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_admin)])
def delete_student(id: int, db: Session = Depends(get_db)):
    StudentService.delete_existing_student(db=db, student_id=id)
    return None
