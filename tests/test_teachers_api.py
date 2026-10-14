def test_create_teacher_success(client):
    payload = {
        "teacher_code": "GV123456",
        "last_name": "Trần",
        "first_name": "Bình",
        "email": "tranbinh@example.com",
        "phone": "0912345678",
        "degree": "Tiến sĩ",
    }
    response = client.post("/api/v1/teachers/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["teacher_code"] == "GV123456"
    assert data["first_name"] == "Bình"


def test_list_teachers(client, sample_teacher):
    response = client.get("/api/v1/teachers/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["teacher_code"] == sample_teacher.teacher_code


def test_get_teacher_by_id(client, sample_teacher):
    response = client.get(f"/api/v1/teachers/{sample_teacher.id}")
    assert response.status_code == 200
    assert response.json()["last_name"] == "Nguyễn"


def test_get_teacher_not_found(client):
    response = client.get("/api/v1/teachers/999")
    assert response.status_code == 404


def test_update_teacher(client, sample_teacher):
    response = client.put(
        f"/api/v1/teachers/{sample_teacher.id}",
        json={"degree": "Phó Giáo sư"},
    )
    assert response.status_code == 200
    assert response.json()["degree"] == "Phó Giáo sư"


def test_delete_teacher(client, sample_teacher):
    response = client.delete(f"/api/v1/teachers/{sample_teacher.id}")
    assert response.status_code == 204
    follow_up = client.get(f"/api/v1/teachers/{sample_teacher.id}")
    assert follow_up.status_code == 404
