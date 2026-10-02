from typing import Optional
from pydantic import BaseModel, Field

class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, description="Tên học sinh")
    class_id: str = Field(..., min_length=1, description="Mã lớp")
    score: float = Field(..., ge=0.0, le=10.0, description="Điểm số từ 0-10")

class StudentCreate(StudentBase):
    pass

# Cập nhật schema dùng cho PUT/PATCH với các trường đều là Optional
class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, description="Tên học sinh")
    class_id: Optional[str] = Field(None, description="Mã lớp")
    score: Optional[float] = Field(None, ge=0.0, le=10.0, description="Điểm số")

class StudentResponse(StudentBase):
    id: int

    class Config:
        from_attributes = True