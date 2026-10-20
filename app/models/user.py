from sqlalchemy import CheckConstraint, Column, Integer, String

from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('admin', 'user')", name="ck_users_role"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False)
    hashed_password = Column(String(60), nullable=False)
    role = Column(String(5), nullable=False, default="user", server_default="user")
