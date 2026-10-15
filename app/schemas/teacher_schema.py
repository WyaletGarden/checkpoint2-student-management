from app.schemas.input_base import InputModel
from pydantic import BaseModel, EmailStr
from typing import Optional

class TeacherCreate(InputModel):
    teacher_code: Optional[str] = None
    last_name: str
    first_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    degree: Optional[str] = None

class TeacherUpdate(InputModel):
    non_nullable_fields = frozenset({'teacher_code', 'last_name', 'first_name'})
    teacher_code: Optional[str] = None
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    degree: Optional[str] = None

class TeacherResponse(BaseModel):
    id: int
    teacher_code: str
    last_name: str
    first_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    degree: Optional[str] = None

    class Config:
        from_attributes = True