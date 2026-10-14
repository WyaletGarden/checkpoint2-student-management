# File: tests/test_students_mock.py
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# Sử dụng @patch để giả lập (mock) toàn bộ hàm create_new_student trong StudentService
@patch("app.services.student_service.StudentService.create_new_student")
def test_create_student_with_mock_db(mock_create_service):
    """
    Test case dùng unittest.mock để cô lập hoàn toàn khỏi Database.
    Hàm create_new_student sẽ không chạy thật mà trả về kết quả giả lập (mock).
    """
    # 1. Thiết lập dữ liệu trả về giả lập (Mock Return Value)
    mock_student_instance = MagicMock()
    mock_student_instance.id = 100
    mock_student_instance.student_code = "MOCK999"
    mock_student_instance.last_name = "Trần Văn"
    mock_student_instance.first_name = "Mock"
    mock_student_instance.email = "tranvanmock@example.com"
    mock_student_instance.phone = "0900000000"
    mock_student_instance.major = "Khoa học máy tính"
    mock_student_instance.score = 9.5
    mock_student_instance.class_id = 1
    mock_student_instance.class_room = None  # Nếu có relationship

    # Gán đối tượng giả lập vào return_value của hàm mock
    mock_create_service.return_value = mock_student_instance

    # 2. Chuẩn bị payload gửi lên API POST
    payload = {
        "student_code": "MOCK999",
        "last_name": "Trần Văn",
        "first_name": "Mock",
        "email": "tranvanmock@example.com",
        "phone": "0900000000",
        "major": "Khoa học máy tính",
        "score": 9.5,
        "class_id": 1
    }

    # 3. Gửi request giả lập tới FastAPI
    response = client.post("/api/v1/students/", json=payload)

    # 4. Kiểm tra kết quả phản hồi từ API
    assert response.status_code in [200, 201]
    data = response.json()
    assert data["student_code"] == "MOCK999"
    assert data["first_name"] == "Mock"
    assert data["score"] == 9.5

    # 5. Xác thực rằng service thực sự đã được gọi đúng 1 lần với đúng luồng nghiệp vụ
    mock_create_service.assert_called_once()