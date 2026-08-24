# Task Tracker API image.
# Build context is the repository root; the application lives in backend/.
FROM python:3.13-slim

# Faster, quieter, no .pyc clutter in the image layer.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv

# Dependencies first so the layer is cached when only source changes.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Only the application package is copied. Tests, venv, and .env are excluded
# by .dockerignore, so no local secrets or virtualenv can be baked in.
COPY backend/app ./app

# Run as an unprivileged user rather than root.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# --host 0.0.0.0 is required for the port to be reachable from outside the
# container. No --reload: that is a local development flag only.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
