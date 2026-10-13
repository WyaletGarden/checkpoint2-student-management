from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    student_code = Column(String, unique=True, index=True, nullable=False)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, nullable=True)
    major = Column(String, nullable=True)
    score = Column(Float, nullable=True)
    
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)

    class_room = relationship("Class", back_populates="students")