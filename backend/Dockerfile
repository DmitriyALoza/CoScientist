FROM python:3.13-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Don't compile packages from source; use pre-built wheels only
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./
COPY .env.example ./.env.example

# Install dependencies (no dev extras)
# pyproject.toml forces torch/torchvision to the CPU-only PyTorch index
# --frozen ensures exact versions from lockfile (reproducible builds)
RUN uv sync --no-dev --frozen

# Copy application code
COPY . .

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
