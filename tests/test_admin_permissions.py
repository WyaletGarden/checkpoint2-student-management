import pytest


@pytest.fixture
def records(sample_student, sample_teacher, sample_class):
    return {
        "students": (sample_student.id, {
            "student_code": "NEW001", "last_name": "New", "first_name": "Student",
            "class_id": sample_class.id, "score": 10,
        }),
        "classes": (sample_class.id, {"class_code": "NEW01", "class_name": "New Class"}),
        "teachers": (sample_teacher.id, {
            "teacher_code": "GVNEW01", "last_name": "New", "first_name": "Teacher",
        }),
    }


@pytest.mark.parametrize("resource", ["students", "classes", "teachers"])
@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
def test_user_cannot_modify_records(user_client, records, resource, method):
    record_id, payload = records[resource]
    base = f"/api/v1/{resource}/"
    before = user_client.get(base).json()
    path = base if method == "POST" else f"{base}{record_id}"
    response = user_client.request(method, path, json=payload if method != "DELETE" else None)
    assert response.status_code == 403
    assert response.json() == {"detail": "Admin role required"}
    assert user_client.get(base).json() == before


@pytest.mark.parametrize("resource", ["students", "classes", "teachers"])
@pytest.mark.parametrize("method", ["PUT", "DELETE"])
def test_user_cannot_modify_missing_records(user_client, resource, method):
    response = user_client.request(method, f"/api/v1/{resource}/999", json={})
    assert response.status_code == 403


@pytest.mark.parametrize("resource", ["students", "classes", "teachers"])
@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
def test_invalid_token_cannot_modify_records(public_client, resource, method):
    suffix = "/" if method == "POST" else "/1"
    response = public_client.request(method, f"/api/v1/{resource}{suffix}", json={},
                                     headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


@pytest.mark.parametrize("resource", ["students", "classes", "teachers"])
def test_user_can_read_list_and_detail(user_client, records, resource):
    record_id, _ = records[resource]
    assert user_client.get(f"/api/v1/{resource}/").status_code == 200
    assert user_client.get(f"/api/v1/{resource}/{record_id}").status_code == 200


def test_demo_requires_admin(user_client, sample_student):
    assert user_client.get("/demo/fixed-n-plus-1").status_code == 403


def test_admin_can_access_demo(admin_client, sample_student):
    response = admin_client.get("/demo/fixed-n-plus-1")
    assert response.status_code == 200
    assert response.json()["total_students"] == 1
