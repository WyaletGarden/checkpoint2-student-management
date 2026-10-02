from pydantic import BaseModel, Field
from typing import Optional

class StudentBase(BaseModel):
    last_name: str = Field(..., description="Họ và tên đệm")
    first_name: str = Field(..., description="Tên chính")
    class_id: str = Field(..., description="Mã lớp")
    score: float = Field(..., ge=0.0, le=10.0, description="Điểm số từ 0 đến 10")

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    last_name: Optional[str] = None
    first_name: Optional[str] = None
    class_id: Optional[str] = None
    score: Optional[float] = Field(None, ge=0.0, le=10.0)

class StudentResponse(StudentBase):
    id: int

    class Config:
        from_attributes = True