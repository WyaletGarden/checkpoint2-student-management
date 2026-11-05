# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Log immediately and avoid creating __pycache__ inside the container.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_URL=sqlite:////data/students.db

WORKDIR /app

# Install dependencies first so source edits can reuse this build layer.
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy the API, bundled frontend, and database migrations.
COPY app/ ./app/
COPY frontend/ ./frontend/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# The app writes SQLite data and logs; only these directories need write access.
RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --no-create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /data /app/logs \
    && chown appuser:appuser /data /app/logs

USER appuser

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
