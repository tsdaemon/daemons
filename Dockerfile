FROM ghcr.io/astral-sh/uv:alpine

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .

RUN uv sync --no-dev --no-install-project

COPY daemons/ ./daemons/
COPY README.md .

RUN uv sync --no-dev

CMD ["uv", "run", "fastapi", "run", "daemons/server.py", "--workers", "10", "--port", "8000"]