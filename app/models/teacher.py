from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    teacher_code = Column(String, unique=True, index=True, nullable=False)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, nullable=True)
    degree = Column(String, nullable=True)

    classes = relationship("Class", back_populates="advisor", cascade="all, delete-orphan")