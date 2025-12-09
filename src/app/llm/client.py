"""LLM client wrapper using LiteLLM for unified API access."""

import json
from functools import lru_cache
from typing import Any, Literal

import litellm
from litellm import completion, embedding

from app.core.config import settings

# Disable verbose logging for litellm
litellm.suppress_debug_info = True


class LLMClient:
    """
    Unified LLM client that supports multiple providers (OpenAI, Claude, etc.).

    Uses LiteLLM to provide a consistent OpenAI-compatible interface
    regardless of the underlying provider.
    """

    def __init__(
        self,
        provider: Literal["openai", "claude"] = "openai",
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        """
        Initialize LLM client.

        Args:
            provider: LLM provider to use (openai or claude)
            model: Model name (if None, uses default from settings)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
        """
        self.provider = provider
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Set API keys based on provider
        if provider == "openai":
            litellm.openai_key = settings.OPENAI_API_KEY
            self.model = model or settings.OPENAI_MODEL
        elif provider == "claude":
            litellm.anthropic_key = settings.ANTHROPIC_API_KEY
            self.model = model or settings.ANTHROPIC_MODEL
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: Literal["text", "json"] = "text",  # 응답 형식
        **kwargs: Any,
    ) -> str:
        """
        Generate chat completion using the configured LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            response_format: Response format (text or json)
            **kwargs: Additional parameters to pass to LiteLLM

        Returns:
            Generated text response

        Example:
            >>> client = LLMClient(provider="openai")
            >>> messages = [
            ...     {"role": "system", "content": "You are a helpful assistant."},
            ...     {"role": "user", "content": "Summarize this article."}
            ... ]
            >>> response = client.chat_completion(messages)
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        # Prepare completion parameters
        completion_params = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": max_tok,
            **kwargs,
        }

        # Add response format for JSON mode
        # openai 만 json 모드를 지원한다. claude의 경우 프롬프트에 json 요청으로 유도해야함
        if response_format == "json":
            if self.provider == "openai":
                completion_params["response_format"] = {"type": "json_object"}
            # Claude doesn't have native JSON mode, but we can add instructions

        try:
            response = completion(**completion_params)  # litellm 함수임
            content = response.choices[0].message.content

            # Validate JSON if requested, json 응답 검증 및 복구
            if response_format == "json":
                try:
                    json.loads(content)
                except json.JSONDecodeError:
                    # If not valid JSON, try to extract JSON from the response
                    import re

                    # json이 아니면 정규 식으로 추출 시도
                    json_match = re.search(r"\{.*\}", content, re.DOTALL)
                    if json_match:
                        content = json_match.group(0)

            return content

        except Exception as e:
            raise RuntimeError(f"LLM completion failed: {e}") from e

    # json형식 사용 예시
    # # OpenAI로 일반 텍스트 요약
    # client = LLMClient(provider="openai")
    # messages = [
    #     {"role": "system", "content": "You are a helpful assistant."},
    #     {"role": "user", "content": "Summarize this article about AI..."}
    # ]
    # summary = client.chat_completion(messages)

    # # JSON 형식으로 분류 결과 받기
    # messages = [
    #     {"role": "system", "content": "Classify articles and return JSON"},
    #     {"role": "user", "content": "Classify: 'GPT-4 paper released'"}
    # ]
    # result = client.chat_completion(
    #     messages,
    #     response_format="json",
    #     temperature=0.0  # 결정적인 응답
    # )
    # # result: '{"category": "paper", "confidence": 0.95}'

    def generate_embedding(self, text: str, model: str | None = None) -> list[float]:
        """
        Generate embedding vector for given text.

        Args:
            text: Input text to embed
            model: Embedding model name (if None, uses default)

        Returns:
            Embedding vector as list of floats

        Example:
            >>> client = LLMClient()
            >>> vec = client.generate_embedding("AI research trends")
            >>> len(vec)
            1536
        """
        embedding_model = model or settings.OPENAI_EMBEDDING_MODEL

        try:
            response = embedding(model=embedding_model, input=text)
            return response.data[0]["embedding"]

        except Exception as e:
            raise RuntimeError(f"Embedding generation failed: {e}") from e

    async def achat_completion(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: Literal["text", "json"] = "text",
        **kwargs: Any,
    ) -> str:
        """
        Async version of chat_completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            response_format: Response format (text or json)
            **kwargs: Additional parameters to pass to LiteLLM

        Returns:
            Generated text response
        """
        temp = temperature if temperature is not None else self.temperature
        max_tok = max_tokens if max_tokens is not None else self.max_tokens

        completion_params = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
            "max_tokens": max_tok,
            **kwargs,
        }

        if response_format == "json" and self.provider == "openai":
            completion_params["response_format"] = {"type": "json_object"}

        try:
            response = await litellm.acompletion(**completion_params)
            content = response.choices[0].message.content

            if response_format == "json":
                try:
                    json.loads(content)
                except json.JSONDecodeError:
                    import re

                    json_match = re.search(r"\{.*\}", content, re.DOTALL)
                    if json_match:
                        content = json_match.group(0)

            return content

        except Exception as e:
            raise RuntimeError(f"Async LLM completion failed: {e}") from e

    async def agenerate_embedding(self, text: str, model: str | None = None) -> list[float]:
        """
        Async version of generate_embedding.

        Args:
            text: Input text to embed
            model: Embedding model name (if None, uses default)

        Returns:
            Embedding vector as list of floats
        """
        embedding_model = model or settings.OPENAI_EMBEDDING_MODEL

        try:
            response = await litellm.aembedding(model=embedding_model, input=text)
            return response.data[0]["embedding"]

        except Exception as e:
            raise RuntimeError(f"Async embedding generation failed: {e}") from e


@lru_cache
def get_llm_client(
    provider: Literal["openai", "claude"] = "openai",
    model: str | None = None,
) -> LLMClient:
    """
    Get cached LLM client instance.

    Args:
        provider: LLM provider to use
        model: Model name (optional)

    Returns:
        Cached LLMClient instance
    """
    return LLMClient(provider=provider, model=model)
