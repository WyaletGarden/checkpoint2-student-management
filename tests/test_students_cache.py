"""Student-list cache behavior through the authenticated API, without Redis."""

from unittest.mock import Mock

import pytest

from app.core.config import settings
from app.models.class_model import Class
from app.models.student import Student
from app.models.teacher import Teacher
from app.schemas.student import StudentResponse, StudentUpdate
from app.services.student_service import StudentService


STUDENTS = "/api/v1/students/"


@pytest.fixture
def list_queries(monkeypatch):
    spy = Mock(wraps=StudentService.get_all_students)
    monkeypatch.setattr(StudentService, "get_all_students", spy)
    return spy


def test_repeated_list_uses_cache_and_keeps_total(client, sample_student, list_queries):
    first = client.get(STUDENTS)
    second = client.get(STUDENTS)

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert second.json()[0]["id"] == sample_student.id
    assert first.headers["X-Total-Count"] == second.headers["X-Total-Count"] == "1"
    assert list_queries.call_count == 1


def test_cached_queries_keep_filters_sort_pages_and_totals_separate(
    client, db, sample_class, list_queries
):
    other_class = Class(class_code="CACHE-OTHER", class_name="Other class")
    db.add(other_class)
    db.flush()
    records = [
        Student(student_code="CACHE-A", last_name="Beta", first_name="Zulu", score=9,
                class_id=sample_class.id),
        Student(student_code="CACHE-B", last_name="Zeta", first_name="Alpha", score=2,
                class_id=sample_class.id),
        Student(student_code="CACHE-C", last_name="Delta", first_name="Echo", score=5,
                class_id=other_class.id),
    ]
    db.add_all(records)
    db.commit()
    a, b, c = [record.id for record in records]
    cases = [
        ({}, [a, b, c], 3),
        ({"class_id": sample_class.id}, [a, b], 2),
        ({"class_id": other_class.id}, [c], 1),
        ({"sort_by": "score_asc"}, [b, c, a], 3),
        ({"sort_by": "score_desc"}, [a, c, b], 3),
        ({"sort_by": "first_name"}, [b, c, a], 3),
        ({"sort_by": "last_name"}, [a, c, b], 3),
        ({"skip": 1}, [b, c], 3),
        ({"limit": 1}, [a], 3),
        ({"q": "CACHE-B"}, [b], 1),
        ({"q": "not-present"}, [], 0),
        ({"skip": 99}, [], 3),
        ({"class_id": sample_class.id, "q": "CACHE", "sort_by": "score_asc",
          "skip": 1, "limit": 1}, [a], 2),
    ]
    for params, ids, total in cases:
        for _ in range(2):
            response = client.get(STUDENTS, params=params)
            assert response.status_code == 200
            assert [student["id"] for student in response.json()] == ids
            assert response.headers["X-Total-Count"] == str(total)
    assert list_queries.call_count == len(cases)


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
def test_student_mutation_refreshes_warm_list(
    client, sample_student, list_queries, method
):
    assert len(client.get(STUDENTS).json()) == 1
    path = STUDENTS if method == "POST" else f"{STUDENTS}{sample_student.id}"
    payload = {
        "POST": {"student_code": "CACHE-NEW", "last_name": "Test", "first_name": "New",
                 "class_id": sample_student.class_id},
        "PUT": {"first_name": "Changed"},
    }.get(method)
    result = client.request(method, path, json=payload)
    assert result.status_code == {"POST": 201, "PUT": 200, "DELETE": 204}[method]

    refreshed = client.get(STUDENTS)
    expected_total = {"POST": 2, "PUT": 1, "DELETE": 0}[method]
    assert refreshed.status_code == 200
    assert refreshed.headers["X-Total-Count"] == str(expected_total)
    assert len(refreshed.json()) == expected_total
    if method == "POST":
        assert refreshed.json()[-1]["student_code"] == "CACHE-NEW"
    elif method == "PUT":
        assert refreshed.json()[0]["first_name"] == "Changed"
    assert client.get(STUDENTS).json() == refreshed.json()
    assert list_queries.call_count == 2


@pytest.mark.parametrize("change", ["name", "assign_advisor", "clear_advisor"])
def test_class_update_refreshes_nested_student_response(
    client, db, sample_student, sample_class, sample_teacher, list_queries, change
):
    sample_class.teacher_id = sample_teacher.id
    other_teacher = Teacher(teacher_code="CACHE-TEACHER", last_name="Other", first_name="Advisor")
    db.add(other_teacher)
    db.commit()
    before = client.get(STUDENTS).json()[0]["class_room"]
    assert before["advisor"]["id"] == sample_teacher.id

    payload = {
        "name": {"class_name": "Renamed class"},
        "assign_advisor": {"teacher_id": other_teacher.id},
        "clear_advisor": {"teacher_id": None},
    }[change]
    assert client.put(f"/api/v1/classes/{sample_class.id}", json=payload).status_code == 200
    after = client.get(STUDENTS).json()[0]["class_room"]
    if change == "name":
        assert after["class_name"] == "Renamed class"
    elif change == "assign_advisor":
        assert after["advisor"]["id"] == other_teacher.id
    else:
        assert after["teacher_id"] is None
        assert after["advisor"] is None
    assert list_queries.call_count == 2


@pytest.mark.parametrize("method", ["PUT", "DELETE"])
def test_teacher_mutation_refreshes_nested_student_response(
    client, db, sample_student, sample_class, sample_teacher, list_queries, method
):
    sample_class.teacher_id = sample_teacher.id
    db.commit()
    assert client.get(STUDENTS).json()[0]["class_room"]["advisor"]["id"] == sample_teacher.id

    result = client.request(method, f"/api/v1/teachers/{sample_teacher.id}",
                            json={"first_name": "Changed advisor"} if method == "PUT" else None)
    assert result.status_code == (200 if method == "PUT" else 204)
    class_room = client.get(STUDENTS).json()[0]["class_room"]
    if method == "PUT":
        assert class_room["advisor"]["first_name"] == "Changed advisor"
    else:
        assert class_room["teacher_id"] is None
        assert class_room["advisor"] is None
    assert list_queries.call_count == 2


def test_redis_read_failure_falls_back_then_recovers(
    client, sample_student, student_cache_redis, list_queries
):
    student_cache_redis.fail_get = True
    response = client.get(STUDENTS)
    assert response.status_code == 200
    assert response.json()[0]["id"] == sample_student.id
    assert response.headers["X-Total-Count"] == "1"

    student_cache_redis.fail_get = False
    assert client.get(STUDENTS).json() == response.json()
    assert client.get(STUDENTS).json() == response.json()
    assert list_queries.call_count == 2


def test_redis_write_failure_keeps_database_results_available(
    client, sample_student, student_cache_redis, list_queries
):
    expected = client.get(STUDENTS).json()
    student_cache_redis.advance(settings.STUDENTS_CACHE_TTL_SECONDS + 1)
    student_cache_redis.fail_set = True
    for _ in range(2):
        response = client.get(STUDENTS)
        assert response.status_code == 200
        assert response.json() == expected
        assert response.headers["X-Total-Count"] == "1"
    assert list_queries.call_count == 3


def test_invalidation_failure_does_not_undo_successful_database_write(
    client, sample_student, student_cache_redis
):
    assert client.get(STUDENTS).status_code == 200
    student_cache_redis.fail_set = True
    result = client.put(f"{STUDENTS}{sample_student.id}", json={"first_name": "Saved"})
    assert result.status_code == 200
    assert result.json()["first_name"] == "Saved"
    assert client.get(f"{STUDENTS}{sample_student.id}").json()["first_name"] == "Saved"

    # While Redis remains unavailable, list reads still reflect the committed DB.
    student_cache_redis.fail_get = True
    assert client.get(STUDENTS).json()[0]["first_name"] == "Saved"


@pytest.mark.parametrize("payload", ["not-json", '{"students":"invalid","total":0}'])
def test_corrupt_cached_page_is_replaced_from_database(
    client, sample_student, student_cache_redis, list_queries, payload
):
    original = client.get(STUDENTS)
    result_keys = list(student_cache_redis.expires)
    assert result_keys, "Student-list results must expire"
    for key in result_keys:
        student_cache_redis.data[key] = payload

    response = client.get(STUDENTS)
    assert response.status_code == 200
    assert response.json() == original.json()
    assert response.headers["X-Total-Count"] == "1"
    assert client.get(STUDENTS).json() == original.json()
    assert list_queries.call_count == 2


def test_cache_expiration_requeries_database(
    client, sample_student, student_cache_redis, list_queries, monkeypatch
):
    monkeypatch.setattr(settings, "STUDENTS_CACHE_TTL_SECONDS", 10)
    assert client.get(STUDENTS).status_code == 200
    student_cache_redis.advance(9)
    assert client.get(STUDENTS).status_code == 200
    assert list_queries.call_count == 1
    student_cache_redis.advance(2)
    assert client.get(STUDENTS).status_code == 200
    assert list_queries.call_count == 2


def test_zero_ttl_disables_cache(
    client, sample_student, student_cache_redis, list_queries, monkeypatch
):
    monkeypatch.setattr(settings, "STUDENTS_CACHE_TTL_SECONDS", 0)
    first = client.get(STUDENTS)
    second = client.get(STUDENTS)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert list_queries.call_count == 2
    assert student_cache_redis.get_calls == student_cache_redis.set_calls == 0


def test_warm_cache_does_not_bypass_authentication(
    client, sample_student, student_cache_redis, list_queries
):
    assert client.get(STUDENTS).status_code == 200
    reads_before = student_cache_redis.get_calls
    for authorization in ("", "Bearer invalid"):
        response = client.get(STUDENTS, headers={"Authorization": authorization})
        assert response.status_code == 401
    assert student_cache_redis.get_calls == reads_before
    assert list_queries.call_count == 1


def test_independent_namespaces_do_not_share_cached_pages(
    client, db, sample_student, list_queries, monkeypatch
):
    monkeypatch.setattr(settings, "STUDENTS_CACHE_NAMESPACE", "first-environment")
    assert client.get(STUDENTS).json()[0]["first_name"] == sample_student.first_name

    # An independent environment must not reuse the first environment's result.
    sample_student.first_name = "Another environment"
    db.commit()
    monkeypatch.setattr(settings, "STUDENTS_CACHE_NAMESPACE", "second-environment")
    assert client.get(STUDENTS).json()[0]["first_name"] == "Another environment"
    assert client.get(STUDENTS).json()[0]["first_name"] == "Another environment"
    assert list_queries.call_count == 2


def test_old_inflight_read_cannot_refill_current_cache_after_mutation(
    client, sample_student, monkeypatch
):
    get_students = StudentService.get_all_students
    calls = 0

    def read_then_update(db, **query):
        nonlocal calls
        calls += 1
        students, total = get_students(db, **query)
        if calls == 1:
            # Snapshot the read before another committed write invalidates it.
            students = [StudentResponse.model_validate(student) for student in students]
            StudentService.update_existing_student(
                db, sample_student.id, StudentUpdate(first_name="After mutation")
            )
        return students, total

    monkeypatch.setattr(StudentService, "get_all_students", read_then_update)
    original_name = sample_student.first_name
    assert client.get(STUDENTS).json()[0]["first_name"] == original_name
    assert client.get(STUDENTS).json()[0]["first_name"] == "After mutation"
    assert client.get(STUDENTS).json()[0]["first_name"] == "After mutation"
    assert calls == 2
