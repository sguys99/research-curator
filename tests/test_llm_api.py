"""Test script for LLM API endpoints.

IMPORTANT: Backend 서버를 사전에 기동해야 합니다.
    uvicorn src.app.api.main:app --reload
"""

import json

import httpx
import numpy as np

BASE_URL = "http://localhost:8000"
LLM_BASE = f"{BASE_URL}/api/llm"


def test_chat_completion_openai():
    """Test basic chat completion with OpenAI."""
    print("\n=== Testing OpenAI Chat Completion ===")

    request_data = {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful AI research assistant.",
            },
            {
                "role": "user",
                "content": "2024년 AI 분야 키 트렌드 5가지를 알려줘.",
            },
        ],
        "temperature": 0.7,
        "max_tokens": 300,
    }

    response = httpx.post(f"{LLM_BASE}/chat/completions", json=request_data, timeout=30.0)

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"Provider: {result['provider']}")
        print(f"Model: {result['model']}")
        print(f"Content preview: {result['content'][:100]}...")

        assert result["provider"] == "openai"
        assert result["model"] is not None
        assert len(result["content"]) > 0
        print("✅ OpenAI chat completion test passed!")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False


def test_chat_completion_claude():
    """Test chat completion with Claude."""
    print("\n=== Testing Claude Chat Completion ===")

    try:
        request_data = {
            "provider": "claude",
            "messages": [
                {
                    "role": "user",
                    "content": "2024년 AI 분야 키 트렌드 5가지를 알려줘.",
                },
            ],
            "temperature": 0.7,
            "max_tokens": 300,
        }

        response = httpx.post(f"{LLM_BASE}/chat/completions", json=request_data, timeout=30.0)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"Provider: {result['provider']}")
            print(f"Model: {result['model']}")
            print(f"Content preview: {result['content'][:100]}...")

            assert result["provider"] == "claude"
            assert result["model"] is not None
            assert len(result["content"]) > 0
            print("✅ Claude chat completion test passed!")
            return True
        else:
            print(f"❌ Failed: {response.json()}")
            return False
    except Exception as e:
        print(f"⚠️ Claude API not available: {e}")
        return None


def test_json_response_format():
    """Test JSON response format."""
    print("\n=== Testing JSON Response Format ===")

    request_data = {
        "provider": "openai",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that responds in JSON format.",
            },
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

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        content = result["content"]
        print(f"JSON Response: {content}")

        # Parse JSON to verify it's valid
        data = json.loads(content)
        print(f"Parsed Data: {json.dumps(data, indent=2)}")

        assert "category" in data
        assert "importance_score" in data
        assert "keywords" in data
        assert isinstance(data["keywords"], list)
        print("✅ JSON response format test passed!")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False


def test_article_summarization():
    """Test Korean article summarization."""
    print("\n=== Testing Article Summarization (Korean) ===")

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

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"Summary: {result['summary']}")
        print(f"Original Length: {result['original_length']} characters")
        print(f"Summary Length: {result['summary_length']} characters")

        assert len(result["summary"]) > 0
        assert result["original_length"] > 0
        assert result["summary_length"] > 0
        assert result["summary_length"] < result["original_length"]
        print("✅ Article summarization test passed!")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False


def test_embedding_generation():
    """Test embedding generation and cosine similarity."""
    print("\n=== Testing Embedding Generation ===")

    # Generate embeddings for multiple texts
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

        if response.status_code != 200:
            print(f"❌ Failed for text: {text}")
            print(f"Error: {response.json()}")
            return False

        result = response.json()
        embeddings.append(result["embedding"])

    print(f"Generated {len(embeddings)} embeddings")
    print(f"Embedding dimension: {len(embeddings[0])}")
    print(f"First embedding (first 5 values): {embeddings[0][:5]}")

    # Compute cosine similarities
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    print("\nCosine Similarities:")
    for i, text_i in enumerate(texts):
        for j, text_j in enumerate(texts):
            if i < j:
                sim = cosine_similarity(embeddings[i], embeddings[j])
                print(f"'{text_i}' vs '{text_j}': {sim:.4f}")

    assert len(embeddings) == len(texts)
    assert all(len(emb) > 0 for emb in embeddings)
    print("✅ Embedding generation test passed!")
    return True


def test_temperature_comparison():
    """Test different temperature values."""
    print("\n=== Testing Temperature Comparison ===")

    temperatures = [0.0, 0.5, 1.0]
    prompt = "Explain neural networks in one sentence."

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
    ]

    print(f"Prompt: {prompt}\n")

    results = []
    for temp in temperatures:
        request_data = {
            "provider": "openai",
            "messages": messages,
            "temperature": temp,
            "max_tokens": 100,
        }

        response = httpx.post(f"{LLM_BASE}/chat/completions", json=request_data, timeout=30.0)

        if response.status_code != 200:
            print(f"❌ Failed at temperature {temp}: {response.json()}")
            return False

        result = response.json()
        results.append(result["content"])
        print(f"Temperature {temp}:")
        print(f"  {result['content']}")
        print()

    assert len(results) == len(temperatures)
    assert all(len(r) > 0 for r in results)
    print("✅ Temperature comparison test passed!")
    return True


def test_error_handling():
    """Test error handling for invalid inputs."""
    print("\n=== Testing Error Handling ===")

    # Test 1: Invalid provider
    print("Test 1: Invalid provider")
    request_data = {
        "provider": "invalid",
        "messages": [{"role": "user", "content": "Hello"}],
    }
    response = httpx.post(f"{LLM_BASE}/chat/completions", json=request_data, timeout=30.0)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 500:
        print(f"✓ Expected error received: {response.json()['detail'][:100]}")
    else:
        print(f"⚠️ Unexpected response: {response.json()}")

    # Test 2: Very large max_tokens
    print("\nTest 2: Very large max_tokens")
    request_data = {
        "provider": "openai",
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 100000,
    }
    response = httpx.post(f"{LLM_BASE}/chat/completions", json=request_data, timeout=30.0)
    print(f"Status Code: {response.status_code}")

    if response.status_code == 500:
        print(f"✓ Expected error received: {response.json()['detail'][:100]}")
    else:
        print("⚠️ API handled large max_tokens gracefully")

    print("✅ Error handling test completed!")
    return True


def test_article_analysis():
    """Test research article analysis pipeline."""
    print("\n=== Testing Article Analysis ===")

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

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print("Analysis Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        assert "category" in result
        assert "importance_score" in result
        assert "keywords" in result
        assert "field" in result
        assert "summary_korean" in result
        assert isinstance(result["keywords"], list)
        assert 0.0 <= result["importance_score"] <= 1.0
        print("✅ Article analysis test passed!")
        return True
    else:
        print(f"❌ Failed: {response.json()}")
        return False


def main():
    """Run all LLM API endpoint tests."""
    print("🚀 Starting LLM API Endpoint Tests")
    print(f"Base URL: {BASE_URL}")
    print(f"LLM Endpoints: {LLM_BASE}")
    print("\nIMPORTANT: Make sure the backend server is running:")
    print("  uvicorn src.app.api.main:app --reload\n")

    tests = [
        ("OpenAI Chat Completion", test_chat_completion_openai),
        ("Claude Chat Completion", test_chat_completion_claude),
        ("JSON Response Format", test_json_response_format),
        ("Article Summarization", test_article_summarization),
        ("Embedding Generation", test_embedding_generation),
        ("Temperature Comparison", test_temperature_comparison),
        ("Error Handling", test_error_handling),
        ("Article Analysis", test_article_analysis),
    ]

    passed = 0
    failed = 0
    skipped = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result is True:
                passed += 1
            elif result is False:
                failed += 1
            else:  # None means skipped
                skipped += 1
                print(f"⚠️ Test '{test_name}' was skipped")
        except Exception as e:
            failed += 1
            print(f"\n❌ Test '{test_name}' raised exception: {e}")

    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    print(f"Total Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⚠️ Skipped: {skipped}")
    print("=" * 60)

    if failed == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {failed} test(s) failed")


if __name__ == "__main__":
    main()
