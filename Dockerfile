FROM python:3.12-slim AS base

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install production dependencies only
RUN uv sync --no-dev --frozen

# Download spaCy model
RUN uv run python -m spacy download en_core_web_sm

# Copy source code
COPY src/ src/

EXPOSE 8000

CMD ["uv", "run", "litscope", "serve"]
