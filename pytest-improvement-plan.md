# Pytest Improvement Plan

## Goal
Improve reliability and speed of backend tests by separating unit/integration/e2e, isolating
external dependencies, and introducing shared pytest infrastructure.

## Current Test Classification (Snapshot)
- unit
  - tests/test_security.py (JWT token creation/verification)
  - tests/test_email_builder.py (template rendering and formatting)
  - tests/test_email_sender.py (SMTP mocked)
  - tests/test_email_digest.py (DB/Email mocked)
- integration
  - tests/test_llm_client.py (OpenAI/Anthropic API keys required)
  - tests/test_processors.py (LLM provider required)
  - tests/test_pipeline.py (LLM provider required)
  - tests/test_api_processors.py (FastAPI + LLM provider required)
  - tests/test_llm_api.py (local API server + LLM provider required)
  - tests/test_day5_vector_db.py (Qdrant + LLM provider required)
- e2e
  - tests/test_auth.py (local API server + DB)
  - tests/test_users.py (local API server + DB)

## External Dependencies & Preconditions
- Local API server required
  - tests/test_llm_api.py
  - tests/test_auth.py
  - tests/test_users.py
- LLM provider API keys required
  - tests/test_llm_client.py (skipif guard present)
  - tests/test_processors.py (no skip guard)
  - tests/test_pipeline.py (no skip guard)
  - tests/test_api_processors.py (no skip guard)
  - tests/test_llm_api.py (no skip guard)
  - tests/test_day5_vector_db.py (no skip guard)
- Qdrant required
  - tests/test_day5_vector_db.py (collection recreate/CRUD/search)
- DB required
  - tests/test_auth.py
  - tests/test_users.py

## Step-by-Step Plan
### 1) Establish pytest infrastructure (completed - initial pass)
- Added `tests/conftest.py` with the following fixtures and helpers:
  - `app`: returns FastAPI app with dependency overrides applied.
  - `client`: `TestClient(app)` for sync API tests.
  - `async_client`: `AsyncClient(app=app, base_url="http://test")` for async API tests.
  - `settings_override`: context manager or fixture to override env/config values.
  - `sample_article`, `sample_articles`: canonical articles for processors/pipeline tests.
  - `sample_user`, `sample_preferences`: user/preferences objects for email/digest tests.
  - `llm_mock`: monkeypatch `LLMClient` methods to deterministic outputs.
  - `qdrant_mock`: monkeypatch vector operations to in-memory stubs.
  - `db_session`: optional, uses test DB URL if provided; wraps each test in rollback.
  - `skip_if_no_llm_key`: skip when required env vars missing.
  - `skip_if_no_qdrant`: skip when Qdrant not reachable.

### 2) Introduce test markers and defaults (completed)
- Added markers: `unit`, `integration`, `e2e`.
- Updated `pyproject.toml` to register markers and default to unit-only via `addopts = "-m unit"`.
- Next: document run instructions in `tests/README.md`.

### 3) Isolate external dependencies
- LLM: mock `LLMClient` / providers for unit tests.
- HTTP: replace `httpx` live calls with `TestClient` or `respx`.
- Qdrant: mock vector operations or run under `@pytest.mark.integration` with env guard.
- Email: continue mocking SMTP at unit level; integration optional.

### 4) Refactor existing tests
- Convert script-style tests to pytest style (no `print`, clear asserts).
- Split unit logic from integration workflow.
- Add `skipif` for missing env vars/services.

### 5) Documentation
- Add `tests/README.md` with:
  - test categories and how to run
  - required env vars
  - optional services (docker compose)
  - expected runtime targets
