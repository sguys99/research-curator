"""Tests for LLM client integration."""

import json
import os

import pytest

from src.app.llm import LLMClient

# Check if API keys are available for integration tests
HAS_OPENAI_KEY = bool(os.getenv("OPENAI_API_KEY"))
HAS_ANTHROPIC_KEY = bool(os.getenv("ANTHROPIC_API_KEY"))


class TestLLMClient:
    """Test LLM client functionality."""

    def test_openai_client_initialization(self):
        """Test OpenAI client initialization."""
        client = LLMClient(provider="openai")
        assert client.provider == "openai"
        assert client.model is not None

    def test_claude_client_initialization(self):
        """Test Claude client initialization."""
        client = LLMClient(provider="claude")
        assert client.provider == "claude"
        assert client.model is not None

    def test_invalid_provider(self):
        """Test initialization with invalid provider."""
        with pytest.raises(ValueError):
            LLMClient(provider="invalid")

    @pytest.mark.skipif(not HAS_OPENAI_KEY, reason="Requires OPENAI_API_KEY")
    def test_openai_chat_completion(self):
        """Test OpenAI chat completion (requires API key)."""
        client = LLMClient(provider="openai")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, World!' in one sentence."},
        ]
        response = client.chat_completion(messages, max_tokens=50)
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.skipif(not HAS_ANTHROPIC_KEY, reason="Requires ANTHROPIC_API_KEY")
    def test_claude_chat_completion(self):
        """Test Claude chat completion (requires API key)."""
        client = LLMClient(provider="claude")
        messages = [
            {"role": "user", "content": "Say 'Hello, World!' in one sentence."},
        ]
        response = client.chat_completion(messages, max_tokens=50)
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.skipif(not HAS_OPENAI_KEY, reason="Requires OPENAI_API_KEY")
    def test_json_response_format(self):
        """Test JSON response format."""
        client = LLMClient(provider="openai")
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant that responds in JSON.",
            },
            {
                "role": "user",
                "content": 'Return a JSON object with a single key "message" and value "Hello".',
            },
        ]
        response = client.chat_completion(messages, response_format="json", max_tokens=100)
        # Should be valid JSON
        data = json.loads(response)
        assert isinstance(data, dict)

    @pytest.mark.skipif(not HAS_OPENAI_KEY, reason="Requires OPENAI_API_KEY")
    def test_generate_embedding(self):
        """Test embedding generation."""
        client = LLMClient(provider="openai")
        text = "AI research trends in 2024"
        embedding = client.generate_embedding(text)
        assert isinstance(embedding, list)
        assert len(embedding) == 1536  # OpenAI embedding size
        assert all(isinstance(x, float) for x in embedding)

    @pytest.mark.skipif(not HAS_OPENAI_KEY, reason="Requires OPENAI_API_KEY")
    @pytest.mark.asyncio
    async def test_async_chat_completion(self):
        """Test async chat completion."""
        client = LLMClient(provider="openai")
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say 'Hello, World!' in one sentence."},
        ]
        response = await client.achat_completion(messages, max_tokens=50)
        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.skipif(not HAS_OPENAI_KEY, reason="Requires OPENAI_API_KEY")
    @pytest.mark.asyncio
    async def test_async_generate_embedding(self):
        """Test async embedding generation."""
        client = LLMClient(provider="openai")
        text = "AI research trends in 2024"
        embedding = await client.agenerate_embedding(text)
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
