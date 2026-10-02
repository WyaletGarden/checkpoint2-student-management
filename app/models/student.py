from sqlalchemy import Column, Integer, String, Float
from app.core.database import Base

class StudentModel(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    last_name = Column(String, index=True, nullable=False)   # Họ và tên đệm (ví dụ: Nguyễn Đức)
    first_name = Column(String, index=True, nullable=False)  # Tên chính (ví dụ: Hùng)
    class_id = Column(String, index=True, nullable=False)
    score = Column(Float, nullable=False)