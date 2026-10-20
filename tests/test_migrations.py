"""Verify that migrations, rather than create_all, can bootstrap a database."""
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError

from app.core.config import settings


def test_initial_migration_round_trip(tmp_path, monkeypatch):
    database_url = f"sqlite:///{(tmp_path / 'migration.db').as_posix()}"
    monkeypatch.setattr(settings, "DATABASE_URL", database_url)
    project_root = Path(__file__).resolve().parents[1]
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "alembic"))

    command.upgrade(config, "head")
    engine = create_engine(database_url)
    try:
        assert set(inspect(engine).get_table_names()) == {
            "alembic_version", "teachers", "classes", "students", "users"
        }
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one() == "b82d4e5f6a70"
        command.check(config)
        # Re-running upgrade must preserve existing records.
        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO teachers (id, teacher_code, last_name, first_name) "
                "VALUES (1, 'GVTEST', 'Migration', 'Test')"
            ))
        command.upgrade(config, "head")
        with engine.connect() as connection:
            assert connection.execute(text("SELECT COUNT(*) FROM teachers")).scalar_one() == 1

        # Downgrade is exercised only against this disposable database.
        command.downgrade(config, "base")
        assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
        command.upgrade(config, "head")
        command.check(config)
    finally:
        engine.dispose()


def test_user_role_migration_preserves_accounts(tmp_path, monkeypatch):
    database_url = f"sqlite:///{(tmp_path / 'roles.db').as_posix()}"
    monkeypatch.setattr(settings, "DATABASE_URL", database_url)
    project_root = Path(__file__).resolve().parents[1]
    config = Config(str(project_root / "alembic.ini"))
    config.set_main_option("script_location", str(project_root / "alembic"))
    command.upgrade(config, "a91c2d3e4f50")
    engine = create_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text(
                "INSERT INTO users (id, username, hashed_password) VALUES (1, 'legacy', 'hash')"
            ))
        command.upgrade(config, "head")
        with engine.begin() as connection:
            assert connection.execute(text(
                "SELECT username, hashed_password, role FROM users WHERE id = 1"
            )).one() == ("legacy", "hash", "user")
            connection.execute(text(
                "INSERT INTO users (id, username, hashed_password) VALUES (2, 'new', 'hash')"
            ))
            assert connection.execute(text(
                "SELECT role FROM users WHERE id = 2"
            )).scalar_one() == "user"
            connection.execute(text("UPDATE users SET role = 'admin' WHERE id = 1"))
        for invalid_role in ["owner", None]:
            with pytest.raises(IntegrityError), engine.begin() as connection:
                connection.execute(text("UPDATE users SET role = :role WHERE id = 1"),
                                   {"role": invalid_role})
        command.downgrade(config, "a91c2d3e4f50")
        assert "role" not in {column["name"] for column in inspect(engine).get_columns("users")}
        with engine.connect() as connection:
            assert connection.execute(text(
                "SELECT username, hashed_password FROM users WHERE id = 1"
            )).one() == ("legacy", "hash")
        command.upgrade(config, "head")
        command.check(config)
    finally:
        engine.dispose()
