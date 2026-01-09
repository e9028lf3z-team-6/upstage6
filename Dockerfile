# =========================
# Base image
# =========================
FROM python:3.12-slim

# =========================
# Environment
# =========================
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# =========================
# Workdir
# =========================
WORKDIR /app

# =========================
# System dependencies
# =========================
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# =========================
# Install uv
# =========================
RUN pip install --no-cache-dir uv

# =========================
# Copy dependency files first (cache optimization)
# =========================
COPY pyproject.toml uv.lock ./

# =========================
# Install dependencies
# =========================
RUN uv sync --no-cache

# =========================
# Copy application source
# =========================
COPY . .

# =========================
# Expose port
# =========================
EXPOSE 8800

# =========================
# Run FastAPI
# =========================
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8800"]
