import pytest

from app.models.class_model import Class
from app.models.student import Student
from app.models.teacher import Teacher


@pytest.mark.parametrize("resource", ["students", "classes", "teachers"])
def test_search_filters_before_pagination_and_counts(client, db, sample_class, resource):
    if resource == "students":
        records = [Student(student_code=f"CODE{i}", last_name="Le", first_name=f"Target{i}",
                           email=f"test{i}@example.com", class_id=sample_class.id) for i in range(3)]
        records.append(Student(student_code="OTHER", last_name="Other", first_name="Person", class_id=sample_class.id))
    elif resource == "teachers":
        records = [Teacher(teacher_code=f"CODE{i}", last_name="Le", first_name=f"Target{i}",
                           email=f"test{i}@example.com") for i in range(3)]
        records.append(Teacher(teacher_code="OTHER", last_name="Other", first_name="Person"))
    else:
        records = [Class(class_code=f"CODE{i}", class_name=f"Target{i}") for i in range(3)]
        records.append(Class(class_code="OTHER", class_name="Other"))
    db.add_all(records)
    db.commit()
    base = f"/api/v1/{resource}/"
    response = client.get(base, params={"q": " target ", "skip": 1, "limit": 1})
    assert response.status_code == 200
    assert response.headers["X-Total-Count"] == "3"
    assert [item["id"] for item in response.json()] == [records[1].id]
    for term in ["CODE1", "code1"]:
        assert len(client.get(base, params={"q": term}).json()) == 1
    for term in ["%", "_", "does-not-exist"]:
        response = client.get(base, params={"q": term})
        assert response.json() == []
        assert response.headers["X-Total-Count"] == "0"
    if resource != "classes":
        assert len(client.get(base, params={"q": "Le Target"}).json()) == 3
        assert len(client.get(base, params={"q": "test1@example.com"}).json()) == 1


def test_student_search_combines_with_class_filter(client, db, sample_class):
    other = Class(class_code="OTHER", class_name="Other")
    db.add(other)
    db.flush()
    db.add_all([Student(student_code="SV1", last_name="Le", first_name="Target", class_id=sample_class.id),
                Student(student_code="SV2", last_name="Le", first_name="Target", class_id=other.id)])
    db.commit()
    response = client.get("/api/v1/students/", params={"q": "Target", "class_id": sample_class.id})
    assert response.headers["X-Total-Count"] == "1"
    assert response.json()[0]["student_code"] == "SV1"
