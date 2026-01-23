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

### 3) Audit and triage (new)
- Create a failing/invalid test inventory:
  - missing asserts, incorrect assertions, or tests that always pass/fail.
  - tests that call live services without guards.
  - tests that are scripts (`main()` blocks) vs pytest style.
- Label each test with a target category: `unit`, `integration`, `e2e`.
- Identify missing coverage areas by module (e.g., CRUD, API validation, error paths).
#### Inventory (initial findings)
- `tests/test_auth.py`
  - Script-style (`main()`); uses `print`/return values instead of asserts.
  - Requires running server; no markers/skip guards.
- `tests/test_users.py`
  - Script-style; test functions expect params that are not pytest fixtures.
  - Requires running server + DB; no markers/skip guards.
- `tests/test_llm_api.py`
  - Script-style; prints/returns booleans; no assertions in error paths.
  - Requires running server + LLM keys; no markers/skip guards.
- `tests/test_processors.py`
  - Live LLM dependency without skip; heavy `print` output.
  - Includes integration "all processors" flow inside unit test file.
- `tests/test_pipeline.py`
  - Live LLM dependency without skip; timing-based asserts (<30s) are flaky.
  - Script-style runner at bottom.
- `tests/test_api_processors.py`
  - Uses `TestClient` but still calls live LLM/embeddings; should be mocked or marked integration.
- `tests/test_vector_db_integration.py`
  - Uses direct sys.path hacking and live Qdrant + LLM.
  - Async tests missing `pytest.mark.asyncio` and bundled in a runner.
#### Additional gaps
- Missing markers on existing tests (`unit/integration/e2e`) which can cause all tests to be skipped by default.
- Missing `tests/README.md` for execution instructions and environment requirements.
- Script-style tests still present (not pytest-compatible): `test_auth.py`, `test_users.py`, `test_llm_api.py`.
- External dependency guards missing on several tests (LLM/Qdrant/HTTP).
- New fixtures in `tests/conftest.py` are not yet adopted in tests.

### 4) Correctness-first refactor (new)
- Fix broken/incorrect tests before expanding coverage:
  - remove side-effect prints and return values in tests.
  - rewrite tests to assert deterministic outputs using mocks/fixtures.
  - ensure async tests use `pytest.mark.asyncio` and await correctly.
- Add explicit `skipif` guards for env/service requirements.
#### Progress
- Refactored `tests/test_processors.py` to pytest style with `llm_mock` and `@pytest.mark.unit`.
- Refactored `tests/test_pipeline.py` to pytest style with fixtures and removed timing-based asserts.
- Refactored `tests/test_api_processors.py` to use `client` + `llm_mock` and added unit markers.
  - Fixed malformed end-to-end/error handling sections and removed script runner.
- Split `tests/test_llm_client.py` into unit vs integration classes with markers and skips.

### 5) Coverage expansion (new)
- Add missing tests for:
  - API validation errors and edge cases (schema-level).
  - processor fallbacks when LLM JSON parsing fails.
  - vector DB failures and error handling paths.
  - auth token edge cases (expired/invalid types).
- Favor unit tests with mocks; keep integration tests minimal.

### 6) External dependency isolation
- LLM: mock `LLMClient` / providers for unit tests.
- HTTP: replace `httpx` live calls with `TestClient` or `respx`.
- Qdrant: mock vector operations or run under `@pytest.mark.integration` with env guard.
- Email: continue mocking SMTP at unit level; integration optional.

### 7) Restructure existing tests
- Convert script-style tests to pytest style (no `print`, clear asserts).
- Split unit logic from integration workflows.
- Apply markers consistently and update test names to reflect behavior.

### 8) Documentation
- Add `tests/README.md` with:
  - test categories and how to run
  - required env vars
  - optional services (docker compose)
  - expected runtime targets
