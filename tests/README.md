# Tests Guide

## Categories
- `unit`: fast, isolated tests with mocks/stubs
- `integration`: requires external services or API keys
- `e2e`: requires a running backend server and database

## Default behavior
`pytest` runs only `unit` tests by default (`addopts = "-m unit"` in `pyproject.toml`).

## Run commands
- unit only:
  - `pytest`
  - `pytest -m unit`
- integration:
  - `pytest -m integration`
- e2e (live server required):
  - `PYTEST_LIVE_SERVER=1 pytest -m e2e`

## Environment variables
- LLM providers:
  - `OPENAI_API_KEY` (required for OpenAI integration/e2e)
  - `ANTHROPIC_API_KEY` (required for Claude integration/e2e)
- Qdrant:
  - `PYTEST_REAL_QDRANT=1` to enable Qdrant integration tests
- Live server:
  - `PYTEST_LIVE_SERVER=1` to run `e2e` tests against `http://localhost:8000`
- Optional DB test session:
  - `TEST_DATABASE_URL` for DB-backed unit tests using `db_session` fixture

## Required services
- Qdrant (integration): `docker compose up -d` or a running Qdrant instance
- Backend API (e2e): `uvicorn src.app.api.main:app --reload`

## Notes
- Integration/e2e tests are skipped automatically if required env vars are missing.
- Use `-m "unit or integration"` to run multiple categories.
