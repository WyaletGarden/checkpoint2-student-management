from app.schemas.input_base import InputModel
from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.teacher_schema import TeacherResponse

class ClassCreate(InputModel):
    class_code: Optional[str] = None
    class_name: str
    teacher_id: Optional[int] = Field(None, gt=0)

class ClassUpdate(InputModel):
    non_nullable_fields = frozenset({'class_code', 'class_name'})
    class_code: Optional[str] = None
    class_name: Optional[str] = None
    teacher_id: Optional[int] = Field(None, gt=0)

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
