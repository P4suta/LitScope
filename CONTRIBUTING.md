# Contributing to LitScope

Thank you for your interest in contributing to LitScope!

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/litscope.git
   cd litscope
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Install the spaCy English model:
   ```bash
   uv pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
   ```

4. Run tests to verify setup:
   ```bash
   uv run pytest
   ```

## Code Quality

We maintain strict code quality standards:

- **100% test coverage** — All code must be covered by tests
- **Type checking** — mypy strict mode (`uv run mypy src/`)
- **Linting** — Ruff (`uv run ruff check src/ tests/`)
- **Formatting** — Ruff (`uv run ruff format src/ tests/`)

Run all checks before submitting a PR:

```bash
uv run pytest --cov=litscope --cov-report=term-missing && uv run ruff check src/ tests/ && uv run mypy src/
```

## Git Conventions

### Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>
```

- **type**: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `ci`, `style`
- **scope**: `ingestion`, `analysis`, `storage`, `api`, `frontend`, `config`
- One logical change per commit — don't mix features, fixes, and refactors

### Branches

- `main` — Stable. No direct commits, PR merges only.
- `develop` — Development integration branch.
- Feature branches: `feat/<scope>/<short-description>`
- Fix branches: `fix/<scope>/<short-description>`

## Development Philosophy

- **Library delegation** — Prefer library methods over naive implementations
- **Minimal loops/branches** — Favor declarative/functional styles
- **TDD** — Write tests first, then implement
- **Document-driven** — Update docs with every implementation change

## Reporting Issues

Please open an issue on GitHub with:
- A clear description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- Environment details (OS, Python version)
