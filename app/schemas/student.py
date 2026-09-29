from pydantic import BaseModel, Field

class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, description="Tên học sinh không được để trống")
    class_id: str = Field(..., min_length=1, description="Mã lớp học")
    score: float = Field(..., ge=0.0, le=10.0, description="Điểm số từ 0 đến 10")

class StudentCreate(StudentBase):
    pass

class StudentUpdate(StudentBase):
    pass

class StudentResponse(StudentBase):
    id: int

    class Config:
        from_attributes = True