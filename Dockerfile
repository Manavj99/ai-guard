FROM python:3.13-slim AS base

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends nodejs npm git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Optional: copy dependency manifests first for better caching
COPY pyproject.toml* requirements.txt* /app/
RUN python -m pip install --upgrade pip \
 && (test -f requirements.txt && pip install -r requirements.txt || true) \
 && (test -f pyproject.toml && pip install ".[all]" || true)

COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* /app/
RUN if [ -f package.json ]; then npm ci || npm i; fi

# Copy source
COPY . /app

# Non-root
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "-m", "ai_guard.cli"]
CMD ["--help"]
