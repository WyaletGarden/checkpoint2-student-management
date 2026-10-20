import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.teacher import Teacher
from app.models.class_model import Class
from app.models.student import Student
from app.models.user import User
from app.core.security import create_access_token

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def _override_db_dependency():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def public_client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def client(public_client, db):
    """Admin client for existing CRUD behavior and validation tests."""
    user = User(username="api-test-user", hashed_password="unused-by-token-tests", role="admin")
    db.add(user)
    db.commit()
    public_client.headers["Authorization"] = f"Bearer {create_access_token(user.id)}"
    return public_client


@pytest.fixture
def user_client(public_client, db):
    user = User(username="regular-test-user", hashed_password="unused", role="user")
    db.add(user)
    db.commit()
    public_client.headers["Authorization"] = f"Bearer {create_access_token(user.id)}"
    return public_client


@pytest.fixture
def admin_client(public_client, db):
    user = User(username="admin-test-user", hashed_password="unused", role="admin")
    db.add(user)
    db.commit()
    public_client.headers["Authorization"] = f"Bearer {create_access_token(user.id)}"
    return public_client


@pytest.fixture
def sample_teacher(db):
    teacher = Teacher(
        teacher_code="GV000001",
        last_name="Nguyễn",
        first_name="An",
        email="nguyenan@example.com",
        phone="0901111111",
        degree="Thạc sĩ",
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@pytest.fixture
def sample_class(db):
    class_room = Class(class_code="CNTT01", class_name="Công nghệ thông tin 1")
    db.add(class_room)
    db.commit()
    db.refresh(class_room)
    return class_room


@pytest.fixture
def sample_student(db, sample_class):
    student = Student(
        student_code="B22DCCN001",
        last_name="Nguyễn Đức",
        first_name="Hùng",
        email="hungnd@example.com",
        phone="0987654321",
        major="Công nghệ thông tin",
        score=8.5,
        class_id=sample_class.id,
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student
