"""End-to-end tests for LLM API endpoints (requires running server)."""

import json
import os

import httpx
import numpy as np
import pytest

BASE_URL = "http://localhost:8000"
LLM_BASE = f"{BASE_URL}/api/llm"

HAS_OPENAI_KEY = bool(os.getenv("OPENAI_API_KEY"))
HAS_ANTHROPIC_KEY = bool(os.getenv("ANTHROPIC_API_KEY"))
LIVE_SERVER = os.getenv("PYTEST_LIVE_SERVER") == "1"


@pytest.mark.e2e
@pytest.mark.skipif(not LIVE_SERVER, reason="Set PYTEST_LIVE_SERVER=1 to run live server tests")
def test_chat_completion_openai():
    request_data = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "You are a helpful AI research assistant."},
            {"role": "user", "content": "2024년 AI 분야 키 트렌드 5가지를 알려줘."},
        ],
        "temperature": 0.7,
        "max_tokens": 300,
    }

    response = httpx.post(f"{LLM_BASE}/chat/completions", json=request_data, timeout=30.0)

    assert response.status_code == 200
    result = response.json()
    assert result["provider"] == "openai"
    assert result["model"]
    assert result["content"]


@pytest.mark.e2e
@pytest.mark.skipif(
    not LIVE_SERVER or not HAS_ANTHROPIC_KEY,
    reason="Requires live server + ANTHROPIC_API_KEY",
)
def test_chat_completion_claude():
    request_data = {
        "provider": "claude",
        "messages": [{"role": "user", "content": "2024년 AI 분야 키 트렌드 5가지를 알려줘."}],
        "temperature": 0.7,
        "max_tokens": 300,
    }

    response = httpx.post(f"{LLM_BASE}/chat/completions", json=request_data, timeout=30.0)

    assert response.status_code == 200
    result = response.json()
    assert result["provider"] == "claude"
    assert result["model"]
    assert result["content"]


@pytest.mark.e2e
@pytest.mark.skipif(
    not LIVE_SERVER or not HAS_OPENAI_KEY,
    reason="Requires live server + OPENAI_API_KEY",
)
def test_json_response_format():
    request_data = {
        "provider": "openai",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that responds in JSON format."},
            {
                "role": "user",
                "content": (
                    "기사 타이틀을 분석하고 다음 기준으로 JSON 포맷으로 정리해줘:\n"
                    "- category: one of (paper, news, report)\n"
                    "- importance_score: 0.0 to 1.0\n"
                    "- keywords: list of 3-5 relevant keywords\n"
                    "- summary: brief one-line summary\n\n"
                    'Title: "GPT-5 Achieves Human-Level Performance on '
                    'Complex Reasoning Tasks"'
                ),
            },
        ],
        "response_format": "json",
        "max_tokens": 300,
    }

    response = httpx.post(f"{LLM_BASE}/chat/completions", json=request_data, timeout=30.0)

    assert response.status_code == 200
    result = response.json()
    data = json.loads(result["content"])
    assert "category" in data
    assert "importance_score" in data
    assert isinstance(data["keywords"], list)


@pytest.mark.e2e
@pytest.mark.skipif(
    not LIVE_SERVER or not HAS_OPENAI_KEY,
    reason="Requires live server + OPENAI_API_KEY",
)
def test_article_summarization():
    article_text = """
    Researchers at MIT have developed a new neural network architecture
    that combines the benefits of transformers with the efficiency of
    convolutional neural networks. The hybrid model, dubbed TransConv,
    achieves state-of-the-art results on image classification tasks while
    requiring 40% less computational resources than traditional transformer
    models. The key innovation lies in the selective attention mechanism
    that adaptively chooses between local and global feature processing
    based on the input characteristics.
    """

    request_data = {
        "provider": "openai",
        "title": "TransConv: Hybrid Architecture for Efficient Image Classification",
        "content": article_text,
        "language": "ko",
        "max_sentences": 4,
    }

    response = httpx.post(f"{LLM_BASE}/summarize", json=request_data, timeout=30.0)

    assert response.status_code == 200
    result = response.json()
    assert result["summary"]
    assert result["original_length"] > 0
    assert result["summary_length"] > 0
    assert result["summary_length"] < result["original_length"]


@pytest.mark.e2e
@pytest.mark.skipif(
    not LIVE_SERVER or not HAS_OPENAI_KEY,
    reason="Requires live server + OPENAI_API_KEY",
)
def test_embedding_generation():
    texts = [
        "Transformer architecture in deep learning",
        "Attention mechanism for neural networks",
        "Reinforcement learning for robotics",
        "Computer vision using CNNs",
    ]

    embeddings = []
    for text in texts:
        request_data = {"text": text}
        response = httpx.post(f"{LLM_BASE}/embeddings", json=request_data, timeout=30.0)
        assert response.status_code == 200
        result = response.json()
        embeddings.append(result["embedding"])

    assert len(embeddings) == len(texts)
    assert all(len(emb) > 0 for emb in embeddings)

    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    sims = [
        cosine_similarity(embeddings[0], embeddings[1]),
        cosine_similarity(embeddings[2], embeddings[3]),
    ]
    assert all(sim > 0 for sim in sims)


@pytest.mark.e2e
@pytest.mark.skipif(
    not LIVE_SERVER or not HAS_OPENAI_KEY,
    reason="Requires live server + OPENAI_API_KEY",
)
def test_temperature_comparison():
    temperatures = [0.0, 0.5, 1.0]
    prompt = "Explain neural networks in one sentence."

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
    ]

    results = []
    for temp in temperatures:
        request_data = {
            "provider": "openai",
            "messages": messages,
            "temperature": temp,
            "max_tokens": 100,
        }

        response = httpx.post(f"{LLM_BASE}/chat/completions", json=request_data, timeout=30.0)
        assert response.status_code == 200
        result = response.json()
        results.append(result["content"])

    assert len(results) == len(temperatures)
    assert all(results)


@pytest.mark.e2e
@pytest.mark.skipif(
    not LIVE_SERVER or not HAS_OPENAI_KEY,
    reason="Requires live server + OPENAI_API_KEY",
)
def test_error_handling():
    request_data = {
        "provider": "invalid",
        "messages": [{"role": "user", "content": "Hello"}],
    }
    response = httpx.post(f"{LLM_BASE}/chat/completions", json=request_data, timeout=30.0)
    assert response.status_code in {400, 422, 500}

    request_data = {
        "provider": "openai",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 100000,
    }
    response = httpx.post(f"{LLM_BASE}/chat/completions", json=request_data, timeout=30.0)
    assert response.status_code in {200, 400, 422, 500}


@pytest.mark.e2e
@pytest.mark.skipif(
    not LIVE_SERVER or not HAS_OPENAI_KEY,
    reason="Requires live server + OPENAI_API_KEY",
)
def test_article_analysis():
    test_article = {
        "title": "Attention Is All You Need",
        "content": """
        The dominant sequence transduction models are based on complex recurrent or
        convolutional neural networks in an encoder-decoder configuration. The best
        performing models also connect the encoder and decoder through an attention
        mechanism. We propose a new simple network architecture, the Transformer,
        based solely on attention mechanisms, dispensing with recurrence and convolutions
        entirely.
        """,
    }

    request_data = {
        "provider": "openai",
        "title": test_article["title"],
        "content": test_article["content"],
    }

    response = httpx.post(f"{LLM_BASE}/analyze", json=request_data, timeout=30.0)

    assert response.status_code == 200
    result = response.json()
    assert "category" in result
    assert "importance_score" in result
    assert "keywords" in result
    assert "field" in result
    assert "summary_korean" in result
    assert isinstance(result["keywords"], list)
    assert 0.0 <= result["importance_score"] <= 1.0
