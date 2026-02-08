FROM python:3.14-slim AS base

ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends nodejs npm git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONPATH=/app/src

# Optional: copy dependency manifests first for better caching
COPY pyproject.toml* requirements.txt* /app/
RUN python -m pip install --upgrade pip \
 && (test -f requirements.txt && pip install -r requirements.txt || true)

# Copy source
COPY . /app

RUN if [ -f pyproject.toml ]; then pip install ".[all]"; fi
RUN if [ -f package.json ]; then npm ci || npm i; fi

# Non-root
ENTRYPOINT ["python", "-m", "ai_guard.analyzer"]
CMD ["--help"]
