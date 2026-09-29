from sqlalchemy import Column, Integer, String, Float
from app.core.database import Base

class StudentModel(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    class_id = Column(String, index=True, nullable=False)
    score = Column(Float, nullable=False)