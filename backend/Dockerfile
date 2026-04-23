# ============================================================================
# IEAP - Intelligent Enterprise Automation Platform
# Multi-stage Production Dockerfile
# ============================================================================

# Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements
COPY requirements.txt .
COPY requirements-dev.txt* .

# Install dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt


# ============================================================================
# Production stage
# ============================================================================
FROM python:3.11-slim as production

# Labels
LABEL org.opencontainers.image.title="IEAP" \
      org.opencontainers.image.description="Intelligent Enterprise Automation Platform" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Enterprise Solutions"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    APP_ENV=production \
    APP_PORT=8000

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 ieap && \
    useradd --uid 1000 --gid ieap --shell /bin/bash --create-home ieap

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=ieap:ieap . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/models && \
    chown -R ieap:ieap /app

# Switch to non-root user
USER ieap

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Default command - run API server
CMD ["uvicorn", "api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]


# ============================================================================
# Development stage
# ============================================================================
FROM production as development

USER root

# Install development dependencies
COPY requirements-dev.txt* .
RUN if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi

# Install additional dev tools
RUN pip install \
    pytest \
    pytest-asyncio \
    pytest-cov \
    httpx \
    ipython \
    black \
    isort \
    mypy \
    ruff

USER ieap

# Development command with hot reload
CMD ["uvicorn", "api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--reload"]


# ============================================================================
# Celery worker stage
# ============================================================================
FROM production as worker

USER ieap

# Run Celery worker
CMD ["celery", "-A", "cache.celery_app:celery_app", "worker", \
     "--loglevel=info", "--concurrency=4", "--prefetch-multiplier=4"]


# ============================================================================
# Celery beat stage (scheduler)
# ============================================================================
FROM production as beat

USER ieap

# Run Celery beat scheduler
CMD ["celery", "-A", "cache.celery_app:celery_app", "beat", \
     "--loglevel=info", "--pidfile=/tmp/celerybeat.pid"]
