from app.schemas.input_base import InputModel
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.schemas.class_schema import ClassResponse

class StudentCreate(InputModel):
    student_code: Optional[str] = None
    last_name: str
    first_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    major: Optional[str] = None
    score: Optional[float] = Field(None, ge=0.0, le=10.0)
    class_id: int = Field(gt=0)

class StudentUpdate(InputModel):
    non_nullable_fields = frozenset({'student_code', 'last_name', 'first_name', 'class_id'})
    student_code: Optional[str] = None
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    major: Optional[str] = None
    score: Optional[float] = Field(None, ge=0.0, le=10.0)
    class_id: Optional[int] = Field(None, gt=0)

class StudentResponse(BaseModel):
    id: int
    student_code: str
    last_name: str
    first_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    major: Optional[str] = None
    score: Optional[float] = None
    class_id: int
    class_room: Optional[ClassResponse] = None

    class Config:
        from_attributes = True