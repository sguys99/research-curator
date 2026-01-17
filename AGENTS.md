# Repository Guidelines

## Project Structure & Module Organization

- `src/app/` contains the backend application code (FastAPI, schedulers, collectors, processors, and utilities).
- `src/app/frontend-poc/` holds the Streamlit UI prototype and related assets.
- `tests/` contains pytest suites; tests are named `test_*.py`.
- `alembic/` and `alembic.ini` manage database migrations.
- `configs/`, `docs/`, and `demo/` host environment settings, documentation, and demos.
- `data/` and `notebooks/` are for local datasets and experiments; they are excluded from pre-commit hooks.

## Build, Test, and Development Commands

- `make init` creates a `.venv` with runtime dependencies via `uv`.
- `make init-dev` installs dev dependencies and pre-commit hooks.
- `make format` runs Ruff lint + format with auto-fixes.
- `docker compose up -d` starts PostgreSQL and Qdrant services.
- `alembic upgrade head` applies database migrations.
- `uvicorn src.app.api.main:app --reload` runs the API locally.
- `streamlit run src/app/frontend/main.py` launches the dashboard.
- `python -m src.app.scheduler.main` runs the data collection scheduler.

## Coding Style & Naming Conventions

- Python 3.12, 4-space indentation, `ruff` for linting/formatting.
- Ruff settings: line length 105, double quotes, isort with `app` as first-party.
- Naming: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE_CASE` for constants.
- Keep modules small; place shared logic in `src/app/utils/` or `src/app/core/`.

## Testing Guidelines

- Frameworks: `pytest` + `pytest-asyncio`.
- Conventions: tests live in `tests/`, names start with `test_`.
- Run all tests: `uv run pytest` (or `pytest` in an activated venv).
- Prefer adding unit tests for new collectors, processors, and API routes.

## Commit & Pull Request Guidelines

- Commit format follows emoji-prefixed summaries seen in history, e.g., `:bug: Fix scheduler status`.
- Keep messages short and imperative; one logical change per commit.
- PRs should include: summary, testing notes/commands, linked issues, and screenshots for UI changes.
- If DB schema changes, include Alembic migration steps and verification notes.

## Security & Configuration Tips

- Copy `.env.example` to `.env` and never commit secrets.
- Required env vars include `OPENAI_API_KEY`, `DATABASE_URL`, and `JWT_SECRET_KEY`.
