import pytest

from app.models.class_model import Class
from app.models.student import Student
from app.models.teacher import Teacher


@pytest.mark.parametrize("group", ["students", "classes", "teachers"])
@pytest.mark.parametrize("params", [
    {"skip": -1}, {"limit": 0}, {"limit": -1}, {"limit": 101},
])
def test_invalid_pagination_returns_422(client, group, params):
    assert client.get(f"/api/v1/{group}/", params=params).status_code == 422


@pytest.mark.parametrize("group", ["students", "classes", "teachers"])
def test_pages_cover_more_than_100_records(client, db, sample_class, group):
    if group == "students":
        records = [Student(student_code=f"SV{i:04}", last_name="Same", first_name="Same",
                           score=8, class_id=sample_class.id) for i in range(105)]
    elif group == "teachers":
        records = [Teacher(teacher_code=f"GV{i:04}", last_name="Same", first_name="Same")
                   for i in range(105)]
    else:
        records = [Class(class_code=f"C{i:04}", class_name="Same") for i in range(104)]
    db.add_all(records)
    db.commit()
    base = f"/api/v1/{group}/"
    first = client.get(base)
    assert first.status_code == 200
    assert len(first.json()) == 100
    assert first.headers["X-Total-Count"] == "105"
    second = client.get(base, params={"skip": 100, "limit": 100})
    assert second.status_code == 200
    assert len(second.json()) == 5
    assert second.headers["X-Total-Count"] == "105"
    ids = [item["id"] for item in first.json() + second.json()]
    assert len(set(ids)) == 105
    assert ids == sorted(ids)
    beyond = client.get(base, params={"skip": 200})
    assert beyond.json() == []
    assert beyond.headers["X-Total-Count"] == "105"


@pytest.mark.parametrize("sort_by", ["first_name", "last_name", "score_asc", "score_desc"])
def test_student_sort_ties_and_filtered_total(client, db, sample_class, sort_by):
    other_class = Class(class_code="OTHER", class_name="Other")
    db.add(other_class)
    db.flush()
    students = [Student(student_code=f"SV{i}", last_name="Same", first_name="Same",
                        score=8, class_id=sample_class.id) for i in range(23)]
    students.append(Student(student_code="OUTSIDE", last_name="Same", first_name="Same",
                            score=8, class_id=other_class.id))
    db.add_all(students)
    db.commit()
    expected = sorted(student.id for student in students[:-1])
    ids = []
    for skip in (0, 20):
        response = client.get("/api/v1/students/", params={
            "class_id": sample_class.id, "sort_by": sort_by, "skip": skip, "limit": 20,
        })
        assert response.status_code == 200
        assert response.headers["X-Total-Count"] == "23"
        ids.extend(item["id"] for item in response.json())
    assert ids == expected


@pytest.mark.parametrize("group", ["students", "classes", "teachers"])
def test_empty_page_has_zero_total(client, group):
    response = client.get(f"/api/v1/{group}/", params={"skip": 0, "limit": 1})
    assert response.status_code == 200
    assert response.json() == []
    assert response.headers["X-Total-Count"] == "0"
