# ==========================================
# Stage 1: Builder
# ==========================================
FROM --platform=linux/amd64 python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==========================================
# Stage 2: Runtime
# ==========================================
FROM --platform=linux/amd64 python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH

ARG ENVIRONMENT
ARG DEBUG
ARG LOG_LEVEL
ARG DATABASE_URL
ARG DATABASE_POOL_SIZE
ARG DATABASE_MAX_OVERFLOW
ARG DATABASE_PORT
ARG DATABASE_NAME
ARG DATABASE_USER
ARG DATABASE_PASSWORD
ARG JWT_SECRET
ARG JWT_ALGORITHM
ARG OPENAI_MODEL
ARG EMBEDDING_MODEL
ARG OPENAI_API_KEY
ARG REDIS_URL
ARG CELERY_BROKER_URL
ARG CELERY_RESULT_BACKEND
ARG API_V1_PREFIX
ARG CORS_ORIGINS
ARG SERVICE_NAME
ARG SERVICE_PORT
ARG NESTJS_API_URL

ENV ENVIRONMENT=${ENVIRONMENT} \
    DEBUG=${DEBUG} \
    LOG_LEVEL=${LOG_LEVEL} \
    DATABASE_URL=${DATABASE_URL} \
    DATABASE_POOL_SIZE=${DATABASE_POOL_SIZE} \
    DATABASE_MAX_OVERFLOW=${DATABASE_MAX_OVERFLOW} \
    DATABASE_PORT=${DATABASE_PORT} \
    DATABASE_NAME=${DATABASE_NAME} \
    DATABASE_USER=${DATABASE_USER} \
    DATABASE_PASSWORD=${DATABASE_PASSWORD} \
    JWT_SECRET=${JWT_SECRET} \
    JWT_ALGORITHM=${JWT_ALGORITHM} \
    OPENAI_MODEL=${OPENAI_MODEL} \
    EMBEDDING_MODEL=${EMBEDDING_MODEL} \
    OPENAI_API_KEY=${OPENAI_API_KEY} \
    REDIS_URL=${REDIS_URL} \
    CELERY_BROKER_URL=${CELERY_BROKER_URL} \
    CELERY_RESULT_BACKEND=${CELERY_RESULT_BACKEND} \
    API_V1_PREFIX=${API_V1_PREFIX} \
    CORS_ORIGINS=${CORS_ORIGINS} \
    SERVICE_NAME=${SERVICE_NAME} \
    SERVICE_PORT=${SERVICE_PORT} \
    NESTJS_API_URL=${NESTJS_API_URL}

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
COPY . .

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE ${SERVICE_PORT:-8000}

ENTRYPOINT ["/app/entrypoint.sh"]