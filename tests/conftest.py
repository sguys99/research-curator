from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


@pytest.fixture
def app(monkeypatch):
    from app.api import main as api_main

    if os.getenv("PYTEST_REAL_QDRANT") != "1":
        monkeypatch.setattr(api_main, "initialize_vector_db", lambda recreate=False: True)

        class _DummyQdrantClient:
            def close(self) -> None:
                return None

        monkeypatch.setattr(api_main, "get_qdrant_client", lambda: _DummyQdrantClient())

    return api_main.app


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
async def async_client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def settings_override(monkeypatch):
    from app.core.config import settings

    def _override(**values):
        for key, value in values.items():
            monkeypatch.setattr(settings, key, value)

    return _override


@pytest.fixture
def sample_article():
    return {
        "title": "Attention Is All You Need",
        "content": "Transformer architecture based solely on attention mechanisms.",
        "source_name": "arXiv",
        "url": "https://arxiv.org/abs/1706.03762",
        "metadata": {"year": 2017, "citations": 50000},
    }


@pytest.fixture
def sample_articles(sample_article):
    return [
        sample_article,
        {
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "content": "BERT introduces bidirectional pretraining for language models.",
            "source_name": "arXiv",
            "url": "https://arxiv.org/abs/1810.04805",
            "metadata": {"year": 2018, "citations": 30000},
        },
    ]


@pytest.fixture
def sample_user():
    from app.db.models import User

    return User(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
    )


@pytest.fixture
def sample_preferences(sample_user):
    from app.db.models import UserPreference

    return UserPreference(
        id=uuid4(),
        user_id=sample_user.id,
        research_fields=["AI", "Machine Learning"],
        keywords=["transformer", "LLM"],
        info_types={"paper": 50, "news": 30, "report": 20},
        daily_limit=5,
    )


@pytest.fixture
def llm_mock(monkeypatch):
    from app.llm.client import LLMClient, get_llm_client

    get_llm_client.cache_clear()

    def _mock_chat_completion(self, messages, response_format="text", **kwargs):
        if response_format == "json":
            return json.dumps(
                {
                    "category": "paper",
                    "confidence": 0.9,
                    "keywords": ["transformer", "attention"],
                    "research_field": "NLP",
                    "innovation": 0.5,
                    "relevance": 0.5,
                    "impact": 0.5,
                    "timeliness": 0.5,
                    "overall_score": 0.5,
                },
            )
        return "mock response"

    async def _mock_achat_completion(self, messages, response_format="text", **kwargs):
        return _mock_chat_completion(self, messages, response_format=response_format, **kwargs)

    def _mock_generate_embedding(self, text, model=None):
        return [0.0] * 1536

    async def _mock_agenerate_embedding(self, text, model=None):
        return [0.0] * 1536

    monkeypatch.setattr(LLMClient, "chat_completion", _mock_chat_completion)
    monkeypatch.setattr(LLMClient, "achat_completion", _mock_achat_completion)
    monkeypatch.setattr(LLMClient, "generate_embedding", _mock_generate_embedding)
    monkeypatch.setattr(LLMClient, "agenerate_embedding", _mock_agenerate_embedding)


@pytest.fixture
def qdrant_mock(monkeypatch):
    from app.vector_db.operations import VectorOperations

    async def _noop_async(*args, **kwargs):
        return []

    def _noop_sync(*args, **kwargs):
        return []

    monkeypatch.setattr(VectorOperations, "search_similar_articles", _noop_async)
    monkeypatch.setattr(VectorOperations, "find_similar_articles", _noop_async)
    monkeypatch.setattr(VectorOperations, "get_articles_batch", _noop_sync)


@pytest.fixture
def skip_if_no_llm_key():
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("LLM API keys not set (OPENAI_API_KEY or ANTHROPIC_API_KEY)")


@pytest.fixture
def skip_if_no_qdrant():
    if os.getenv("PYTEST_REAL_QDRANT") != "1":
        pytest.skip("Qdrant disabled. Set PYTEST_REAL_QDRANT=1 to enable.")


@pytest.fixture
def db_session():
    test_db_url = os.getenv("TEST_DATABASE_URL")
    if not test_db_url:
        pytest.skip("TEST_DATABASE_URL not set")

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(test_db_url)
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    session = SessionLocal()
    transaction = session.begin()
    try:
        yield session
    finally:
        transaction.rollback()
        session.close()
        engine.dispose()
