def test_create_class_success(client, sample_teacher):
    payload = {
        "class_code": "CNTT02",
        "class_name": "Công nghệ thông tin 2",
        "teacher_id": sample_teacher.id,
    }
    response = client.post("/api/v1/classes/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["class_code"] == "CNTT02"
    assert data["teacher_id"] == sample_teacher.id
    assert data["advisor"]["first_name"] == sample_teacher.first_name


def test_create_class_teacher_not_found(client):
    response = client.post(
        "/api/v1/classes/",
        json={"class_name": "Lớp lỗi", "teacher_id": 999},
    )
    assert response.status_code == 400


def test_list_classes(client, sample_class):
    response = client.get("/api/v1/classes/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["class_code"] == sample_class.class_code


def test_get_class_by_id(client, sample_class):
    response = client.get(f"/api/v1/classes/{sample_class.id}")
    assert response.status_code == 200
    assert response.json()["class_name"] == sample_class.class_name


def test_get_class_not_found(client):
    response = client.get("/api/v1/classes/999")
    assert response.status_code == 404


def test_update_class(client, sample_class, sample_teacher):
    response = client.put(
        f"/api/v1/classes/{sample_class.id}",
        json={"class_name": "CNTT Việt-Nhật", "teacher_id": sample_teacher.id},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["class_name"] == "CNTT Việt-Nhật"
    assert data["teacher_id"] == sample_teacher.id


def test_delete_class(client, sample_class):
    response = client.delete(f"/api/v1/classes/{sample_class.id}")
    assert response.status_code == 204
    follow_up = client.get(f"/api/v1/classes/{sample_class.id}")
    assert follow_up.status_code == 404
