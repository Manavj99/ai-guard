# ---------- Base runtime ----------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# git is needed for diff scoping; ca-certificates for HTTPS during pip installs
RUN apt-get update && apt-get install -y --no-install-recommends \
      git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd -m appuser
WORKDIR /app

# Install Python deps first to maximize build cache
# Keep these COPY lines minimal; they invalidate cache only when these files change
COPY requirements.txt pyproject.toml setup.py README.md ai-guard.toml /app/

RUN python -m pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy source and install the package
COPY src /app/src
RUN pip install .

# Workspace is where you'll mount the target repo to scan
WORKDIR /workspace
USER appuser

# Default to the CLI. Pass flags at `docker run` time.
ENTRYPOINT ["python", "-m", "ai_guard.analyzer"]
