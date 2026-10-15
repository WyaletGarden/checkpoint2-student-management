"""Regression coverage for conflicts and partial update validation."""
import pytest


@pytest.fixture(params=["students", "classes", "teachers"])
def resource(request, sample_student, sample_teacher, sample_class):
    group = request.param
    if group == "students":
        return group, sample_student.id, {
            "student_code": "SECOND", "last_name": "Test", "first_name": "Other",
            "email": "other.student@example.com", "class_id": sample_class.id,
        }, ["student_code", "email"], ["student_code", "last_name", "first_name", "class_id"]
    if group == "teachers":
        return group, sample_teacher.id, {
            "teacher_code": "GVSECOND", "last_name": "Test", "first_name": "Other",
            "email": "other.teacher@example.com",
        }, ["teacher_code", "email"], ["teacher_code", "last_name", "first_name"]
    return group, sample_class.id, {
        "class_code": "SECOND", "class_name": "Other class", "teacher_id": sample_teacher.id,
    }, ["class_code"], ["class_code", "class_name"]


def test_duplicate_create_returns_conflict_without_inserting(client, resource):
    group, existing_id, payload, unique_fields, _ = resource
    base = f"/api/v1/{group}/"
    original = client.get(f"{base}{existing_id}").json()
    count = len(client.get(base).json())
    for field in unique_fields:
        duplicate = {**payload, field: original[field]}
        response = client.post(base, json=duplicate)
        assert response.status_code == 409
        assert "detail" in response.json()
        assert len(client.get(base).json()) == count
    # A failed transaction must not prevent subsequent valid writes.
    assert client.post(base, json=payload).status_code == 201


def test_duplicate_update_is_atomic_and_session_recovers(client, resource):
    group, existing_id, payload, unique_fields, _ = resource
    base = f"/api/v1/{group}/"
    original = client.get(f"{base}{existing_id}").json()
    created = client.post(base, json=payload)
    assert created.status_code == 201
    second = created.json()
    url = f"{base}{second['id']}"
    name_field = "class_name" if group == "classes" else "first_name"
    for field in unique_fields:
        response = client.put(url, json={field: original[field], name_field: "Must rollback"})
        assert response.status_code == 409
        assert client.get(url).json() == second
    response = client.put(url, json={name_field: "Recovered"})
    assert response.status_code == 200
    assert response.json()[name_field] == "Recovered"
    # Reusing the same record's own unique values is allowed.
    assert client.put(url, json={f: second[f] for f in unique_fields}).status_code == 200


def test_update_rejects_null_required_fields_without_changes(client, resource):
    group, record_id, _, _, required_fields = resource
    url = f"/api/v1/{group}/{record_id}"
    before = client.get(url).json()
    for field in required_fields:
        response = client.put(url, json={field: None})
        assert response.status_code == 422
        assert client.get(url).json() == before
    # Omitted fields remain unchanged, unlike explicitly supplied null.
    response = client.put(url, json={})
    assert response.status_code == 200
    assert response.json() == before


@pytest.mark.parametrize("bad_value", ["", "   ", "x" * 256])
def test_create_and_update_reject_invalid_names_and_codes(client, resource, bad_value):
    group, record_id, payload, _, required_fields = resource
    base = f"/api/v1/{group}/"
    before = client.get(f"{base}{record_id}").json()
    for field in required_fields:
        if field.endswith("_id"):
            continue
        assert client.post(base, json={**payload, field: bad_value}).status_code == 422
        assert client.put(f"{base}{record_id}", json={field: bad_value}).status_code == 422
    assert client.get(f"{base}{record_id}").json() == before


def test_optional_fields_can_be_cleared_and_names_are_trimmed(client, resource):
    group, record_id, _, _, _ = resource
    url = f"/api/v1/{group}/{record_id}"
    before = client.get(url).json()
    if group == "classes":
        teacher_id = client.get("/api/v1/teachers/").json()[0]["id"]
        assert client.put(url, json={"teacher_id": teacher_id}).status_code == 200
        payload = {"teacher_id": None, "class_name": "  Updated  "}
        name_field = "class_name"
    else:
        payload = {"email": None, "phone": None, "first_name": "  Updated  "}
        name_field = "first_name"
        payload.update({"major": None, "score": None} if group == "students" else {"degree": None})
    response = client.put(url, json=payload)
    assert response.status_code == 200
    data = response.json()
    for field, value in payload.items():
        assert data[field] == ("Updated" if field == name_field else value)
    code_field = {"students": "student_code", "teachers": "teacher_code", "classes": "class_code"}[group]
    assert data[code_field] == before[code_field]


def test_create_trims_names_and_codes(client, resource):
    group, _, payload, _, required_fields = resource
    padded = {
        field: f"  {value}  " if field in required_fields and isinstance(value, str) else value
        for field, value in payload.items()
    }
    response = client.post(f"/api/v1/{group}/", json=padded)
    assert response.status_code == 201
    for field in required_fields:
        assert response.json()[field] == payload[field]


@pytest.mark.parametrize("bad_id", [0, -1])
def test_related_ids_must_be_positive(client, resource, bad_id):
    group, record_id, payload, _, _ = resource
    if group == "teachers":
        return
    field = "class_id" if group == "students" else "teacher_id"
    base = f"/api/v1/{group}/"
    assert client.post(base, json={**payload, field: bad_id}).status_code == 422
    assert client.put(f"{base}{record_id}", json={field: bad_id}).status_code == 422
