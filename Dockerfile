# Build context: repo root (so it can COPY both agents/ and backend/).
# Build with: docker build -f backend/Dockerfile -t pulseai-backend .
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps needed by some Python wheels (reportlab uses zlib, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the agents package and install it
COPY pyproject.toml /app/
COPY agents /app/agents
COPY config /app/config
COPY sources /app/sources
RUN pip install --no-cache-dir -e /app

# Copy the backend package and install it
COPY backend /app/backend
RUN pip install --no-cache-dir -e /app/backend

ENV PORT=8080
EXPOSE 8080

# Cloud Run sets $PORT; uvicorn reads it
WORKDIR /app/backend
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
