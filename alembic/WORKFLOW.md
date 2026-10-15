# Schema migrations

Application and Alembic both use `settings.DATABASE_URL`, loaded from the
environment or `.env`. Do not put credentials in `alembic.ini`.

## Existing local database

The initial revision `f732250e75d4` now contains the full schema. This replaces
the formerly empty revision for this project's local baseline. A database
already at that revision will not execute it again.

Back up your database, then verify its revision and schema:

```powershell
uv run alembic current
uv run alembic check
uv run python -m pytest -q
```

Expected: `f732250e75d4 (head)` and no new upgrade operations detected.
If check reports differences, review them before creating a corrective migration.
Do not downgrade, stamp, or delete the existing database to resolve differences.

## New database and application startup

Configure DATABASE_URL for the intended database, then run:

```powershell
uv run alembic upgrade head
uv run alembic check
uv run fastapi dev app/main.py
```

Run migrations once as a deployment step, before starting application workers.
Importing the application no longer creates tables.

## Future model changes

```powershell
uv run alembic revision --autogenerate -m "describe schema change"
# Review generated operations and any data conversion requirements.
uv run alembic upgrade head
uv run alembic check
```

Do not rewrite revisions after they have been shared or deployed.

## Migration verification

`tests/test_migrations.py` tests an empty temporary SQLite database, compares
the resulting schema to ORM metadata, checks repeated upgrades preserve data,
and exercises downgrade/upgrade only on that disposable database.

Also validate PostgreSQL before deployment: point DATABASE_URL at a newly
created, empty disposable PostgreSQL database, run `upgrade head` and `check`,
then restore the original environment setting. SQLite tests alone do not
verify PostgreSQL-specific behavior. Never run downgrade on the real database
as part of verification.
