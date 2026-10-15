from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    class_code = Column(String, unique=True, index=True, nullable=False)  # Mã lớp
    class_name = Column(String, nullable=False)                           # Tên lớp
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=True) # Cố vấn học tập (Giảng viên)

    advisor = relationship("Teacher", back_populates="classes")
    # Students must be transferred or explicitly deleted before deleting a class.
    students = relationship("Student", back_populates="class_room")
