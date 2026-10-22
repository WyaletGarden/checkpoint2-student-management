from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import require_admin
from app.schemas.student import StudentCreate, StudentUpdate, StudentResponse, StudentSort
from app.services.student_service import StudentService

router = APIRouter(prefix="/students", tags=["Students"])

@router.get("/", response_model=list[StudentResponse])
def get_students(
    response: Response,
    class_id: int | None = None,
    sort_by: StudentSort | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    q: str | None = Query(None, max_length=100),
    db: Session = Depends(get_db)
):
    students, total = StudentService.get_all_students(
        db, class_id=class_id, sort_by=sort_by, skip=skip, limit=limit, q=q
    )
    response.headers["X-Total-Count"] = str(total)
    return students

@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: int, db: Session = Depends(get_db)):
    return StudentService.get_student_by_id(db, student_id=student_id)

@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(require_admin)])
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    return StudentService.create_new_student(db=db, student_in=student)

@router.put("/{student_id}", response_model=StudentResponse, dependencies=[Depends(require_admin)])
def update_student(student_id: int, student: StudentUpdate, db: Session = Depends(get_db)):
    return StudentService.update_existing_student(db=db, student_id=student_id, student_in=student)

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(require_admin)])
def delete_student(student_id: int, db: Session = Depends(get_db)):
    StudentService.delete_existing_student(db=db, student_id=student_id)
    return None
