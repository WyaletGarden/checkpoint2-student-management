def test_create_student_success(client, sample_class):
    payload = {
        "student_code": "B22DCCN001",
        "last_name": "Nguyễn Đức",
        "first_name": "Hùng",
        "email": "hungnd@example.com",
        "phone": "0987654321",
        "major": "Công nghệ thông tin",
        "score": 8.5,
        "class_id": sample_class.id,
    }

    response = client.post("/api/v1/students/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["student_code"] == "B22DCCN001"
    assert data["first_name"] == "Hùng"


def test_create_student_validation_error(client):
    response = client.post("/api/v1/students/", json={"email": "invalid-email-format"})
    assert response.status_code == 422


def test_create_student_class_not_found(client):
    payload = {
        "last_name": "Lê",
        "first_name": "Nam",
        "class_id": 999,
    }
    response = client.post("/api/v1/students/", json=payload)
    assert response.status_code == 400


def test_list_students(client, sample_student):
    response = client.get("/api/v1/students/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["student_code"] == sample_student.student_code


def test_get_student_by_id(client, sample_student):
    response = client.get(f"/api/v1/students/{sample_student.id}")
    assert response.status_code == 200
    assert response.json()["id"] == sample_student.id
    assert response.json()["first_name"] == "Hùng"


def test_get_student_not_found(client):
    response = client.get("/api/v1/students/999")
    assert response.status_code == 404


def test_update_student(client, sample_student):
    response = client.put(
        f"/api/v1/students/{sample_student.id}",
        json={"first_name": "Minh", "score": 9.0},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Minh"
    assert data["score"] == 9.0


def test_delete_student(admin_client, sample_student):
    client = admin_client
    response = client.delete(f"/api/v1/students/{sample_student.id}")
    assert response.status_code == 204
    follow_up = client.get(f"/api/v1/students/{sample_student.id}")
    assert follow_up.status_code == 404
