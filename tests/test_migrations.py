"""Verify that migrations, rather than create_all, can bootstrap a database."""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

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
            "alembic_version", "teachers", "classes", "students"
        }
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT version_num FROM alembic_version")
            ).scalar_one() == "f732250e75d4"
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
