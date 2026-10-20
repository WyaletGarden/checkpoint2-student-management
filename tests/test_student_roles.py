import pytest

from app.core.security import create_access_token
from app.models.student import Student
from app.models.user import User


@pytest.mark.parametrize("existing", [True, False])
def test_regular_user_cannot_delete(user_client, db, sample_student, existing):
    student_id = sample_student.id if existing else sample_student.id + 1000
    response = user_client.delete(f"/api/v1/students/{student_id}")
    assert response.status_code == 403
    assert response.json() == {"detail": "Admin role required"}
    assert db.get(Student, sample_student.id) is not None


def test_admin_delete_missing_student(admin_client):
    assert admin_client.delete("/api/v1/students/999").status_code == 404


def test_role_changes_apply_to_existing_token(public_client, db, sample_student):
    user = User(username="changing-role", hashed_password="unused")
    db.add(user)
    db.commit()
    headers = {"Authorization": f"Bearer {create_access_token(user.id)}"}
    path = f"/api/v1/students/{sample_student.id}"
    assert public_client.delete(path, headers=headers).status_code == 403

    user.role = "admin"
    db.commit()
    assert public_client.delete("/api/v1/students/999", headers=headers).status_code == 404

    user.role = "user"
    db.commit()
    assert public_client.delete(path, headers=headers).status_code == 403
    assert db.get(Student, sample_student.id) is not None


def test_token_role_claim_cannot_override_database_role(public_client, db, sample_student):
    from datetime import datetime, timedelta, timezone
    import jwt
    from app.core.config import settings

    user = User(username="claimed-admin", hashed_password="unused")
    db.add(user)
    db.commit()
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {"sub": str(user.id), "iat": now, "exp": now + timedelta(minutes=5),
         "role": "admin"},
        settings.JWT_SECRET_KEY.get_secret_value(), algorithm="HS256",
    )
    response = public_client.delete(
        f"/api/v1/students/{sample_student.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert db.get(Student, sample_student.id) is not None
