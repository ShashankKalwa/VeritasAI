# ── VeritasAI Backend — FastAPI + Uvicorn ──────────────────────
FROM python:3.12-slim AS base

WORKDIR /app

# System deps needed for trafilatura, lxml, pdf parsing etc.
RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      libxml2-dev \
      libxslt1-dev \
      curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first — leverages Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Non-root user for security
RUN useradd --create-home appuser
USER appuser

# Render will set the PORT environment variable, locally we default to 8000.
# We don't hardcode EXPOSE 8000 because Render assigns it dynamically.

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Shell form allows us to evaluate the $PORT environment variable
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
