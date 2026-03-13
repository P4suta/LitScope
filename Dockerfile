FROM python:3.12-slim AS base

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock README.md ./

# Install production dependencies only (skip project itself — src/ not yet available)
RUN uv sync --no-dev --frozen --no-install-project

# Download spaCy models
RUN uv pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl https://github.com/explosion/spacy-models/releases/download/en_core_web_md-3.8.0/en_core_web_md-3.8.0-py3-none-any.whl

# Copy source code and install project
COPY src/ src/
RUN uv sync --no-dev --frozen

EXPOSE 8000

CMD ["uv", "run", "litscope", "serve"]
