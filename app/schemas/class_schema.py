from pydantic import BaseModel
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.teacher_schema import TeacherResponse

class ClassCreate(BaseModel):
    class_code: Optional[str] = None
    class_name: str
    teacher_id: Optional[int] = None

class ClassUpdate(BaseModel):
    class_code: Optional[str] = None
    class_name: Optional[str] = None
    teacher_id: Optional[int] = None

class ClassResponse(BaseModel):
    id: int
    class_code: str
    class_name: str
    teacher_id: Optional[int] = None
    advisor: Optional["TeacherResponse"] = None

    class Config:
        from_attributes = True

# Tránh lỗi circular import khi Pydantic build model forward references
from app.schemas.teacher_schema import TeacherResponse
ClassResponse.model_rebuild()