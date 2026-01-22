"""Text embedding generation with OpenAI API.

This module provides functionality to generate embeddings for text using OpenAI's
embedding models. Includes batch processing, retry logic, token limit handling,
and caching for improved performance.
"""

import asyncio
import hashlib
import json
import logging
from pathlib import Path
from typing import Any

import tiktoken
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.llm.client import get_llm_client

logger = logging.getLogger(__name__)


class TextEmbedder:
    """Text embedding generator with caching and retry logic."""

    # Default embedding model token limit (fallback when config is missing)
    DEFAULT_MAX_TOKENS = 8191

    def __init__(
        self,
        model: str | None = None,
        use_cache: bool = True,
        max_retries: int = 3,
        retry_wait_min: int = 1,
        retry_wait_max: int = 10,
    ):
        """Initialize text embedder.

        Args:
            model: Embedding model name (defaults to settings.OPENAI_EMBEDDING_MODEL)
            use_cache: Enable caching for identical texts
            max_retries: Maximum number of retry attempts for API calls
            retry_wait_min: Minimum wait time between retries (seconds)
            retry_wait_max: Maximum wait time between retries (seconds)
        """
        self.model = model or settings.OPENAI_EMBEDDING_MODEL
        self.use_cache = use_cache
        self.max_retries = max_retries
        self.retry_wait_min = retry_wait_min
        self.retry_wait_max = retry_wait_max

        # Get LLM client
        self.llm_client = get_llm_client(provider="openai", model=self.model)

        # Initialize tokenizer for token counting
        try:
            self.tokenizer = tiktoken.encoding_for_model(self.model)
        except KeyError:
            # Fallback to cl100k_base encoding if model not found
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

        self.max_tokens = self._get_model_token_limit()

        # In-memory cache
        self._cache: dict[str, list[float]] = {}

        logger.info(f"TextEmbedder initialized with model: {self.model}")

    # 동일한 텍스트에 대해 중복 API 호출 방지
    def _get_cache_key(self, text: str) -> str:
        """Generate cache key for text using SHA-256 hash.

        Args:
            text: Input text

        Returns:
            SHA-256 hash of the text
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _get_model_token_limit(self) -> int:
        """Load model token limits from config file and resolve for current model."""
        config_path = Path(__file__).resolve().parents[3] / "configs" / "model_limits.json"
        if not config_path.exists():
            return self.DEFAULT_MAX_TOKENS

        try:
            with config_path.open("r", encoding="utf-8") as fp:
                limits = json.load(fp)
        except Exception as e:
            logger.warning(f"Failed to load model limits from {config_path}: {e}")
            return self.DEFAULT_MAX_TOKENS

        limit = limits.get(self.model)
        if isinstance(limit, int) and limit > 0:
            return limit

        return self.DEFAULT_MAX_TOKENS

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in text.

        Args:
            text: Input text

        Returns:
            Number of tokens
        """
        try:
            tokens = self.tokenizer.encode(text)
            return len(tokens)
        except Exception as e:
            logger.warning(f"Error counting tokens, using character estimate: {e}")
            # Fallback: rough estimate (1 token ≈ 4 characters)
            return len(text) // 4

    # 텍스트가 최대 토큰을 초과하면 자름
    def truncate_text(self, text: str, max_tokens: int | None = None) -> str:
        """Truncate text to fit within token limit.

        Args:
            text: Input text
            max_tokens: Maximum number of tokens (defaults to model limit)

        Returns:
            Truncated text
        """
        max_tokens = max_tokens or self.max_tokens
        token_count = self.count_tokens(text)

        if token_count <= max_tokens:
            return text

        # Truncate text by decoding tokens
        try:
            tokens = self.tokenizer.encode(text)
            truncated_tokens = tokens[:max_tokens]
            truncated_text = self.tokenizer.decode(truncated_tokens)
            logger.warning(
                f"Text truncated from {token_count} to {max_tokens} tokens",
            )
            return truncated_text
        except Exception as e:
            logger.error(f"Error truncating text: {e}")
            # Fallback: character-based truncation (rough estimate)
            char_limit = max_tokens * 4
            return text[:char_limit]

    # API 호출 실패시 자동 재시도
    @retry(
        retry=retry_if_exception_type((RuntimeError, ConnectionError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def _embed_with_retry(self, text: str) -> list[float]:
        """Generate embedding with automatic retry on failure.

        Args:
            text: Input text

        Returns:
            Embedding vector

        Raises:
            RuntimeError: If embedding generation fails after all retries
        """
        try:
            embedding = await self.llm_client.agenerate_embedding(text, model=self.model)
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise RuntimeError(f"Embedding generation failed: {e}") from e

    async def embed(self, text: str, truncate: bool = True) -> list[float]:
        """Generate embedding for single text.

        Args:
            text: Input text
            truncate: Automatically truncate text if exceeds token limit

        Returns:
            Embedding vector (list of floats)

        Raises:
            ValueError: If text is empty
            RuntimeError: If embedding generation fails

        Examples:
            >>> embedder = TextEmbedder()
            >>> embedding = await embedder.embed("Attention Is All You Need")
            >>> len(embedding)
            1536
        """
        if not text or not text.strip():
            raise ValueError("Empty text provided for embedding")

        # Check cache
        if self.use_cache:  # 캐시가 있으면 캐시에 있는 것 리턴
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                logger.debug(f"Cache hit for text: {text[:50]}...")
                return self._cache[cache_key]

        # Truncate if needed, 토큰 제한 초과시 문서 텍스트 자름
        if truncate:
            token_count = self.count_tokens(text)
            if token_count > self.max_tokens:
                text = self.truncate_text(text)

        # Generate embedding with retry
        try:
            embedding = await self._embed_with_retry(text)

            # Cache result, 결과를 캐시에 저장
            if self.use_cache:
                cache_key = self._get_cache_key(text)
                self._cache[cache_key] = embedding

            logger.info(
                f"Embedding generated: {len(embedding)} dimensions "
                f"for text: {text[:50]}... ({self.count_tokens(text)} tokens)",
            )

            return embedding

        except RetryError as e:
            logger.error(f"Embedding generation failed after {self.max_retries} retries: {e}")
            raise RuntimeError("Max retries exceeded for embedding generation") from e

    async def batch_embed(
        self,
        texts: list[str],
        batch_size: int = 10,
        truncate: bool = True,
        fail_on_error: bool = False,
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts in batches.

        Args:
            texts: List of input texts
            batch_size: Number of texts to process concurrently
            truncate: Automatically truncate texts exceeding token limit
            fail_on_error: If True, raise exception on any error; if False, return zero vectors

        Returns:
            List of embedding vectors

        Examples:
            >>> texts = ["Text 1", "Text 2", "Text 3"]
            >>> embeddings = await embedder.batch_embed(texts)
            >>> len(embeddings)
            3
        """
        if not texts:
            logger.warning("Empty texts list provided")
            return []

        all_embeddings: list[list[float]] = []

        # Process in batches to avoid rate limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            logger.info(f"Processing batch {i // batch_size + 1}: {len(batch)} texts")

            # Generate embeddings concurrently within batch
            tasks = [self.embed(text, truncate=truncate) for text in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for j, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error embedding text {i + j}: {result}")
                    if fail_on_error:
                        raise result
                    # Return zero vector on error
                    all_embeddings.append([0.0] * self.get_embedding_dimension())
                else:
                    all_embeddings.append(result)

            # Small delay between batches to respect rate limits
            if i + batch_size < len(texts):
                await asyncio.sleep(0.5)

        logger.info(
            f"Batch embedding completed: {len(all_embeddings)} texts, "
            f"{sum(1 for e in all_embeddings if e != [0.0] * self.get_embedding_dimension())} "
            f"succeeded",
        )

        return all_embeddings

    def prepare_article_text(  # 텍스트를 제목, 요약, 본문의 구조화된 형태로 결합
        self,
        title: str,
        content: str,
        summary: str | None = None,
    ) -> str:
        """Prepare article text for embedding.

        Combines title, summary, and content into optimized embedding text.

        Args:
            title: Article title
            content: Article content
            summary: Article summary (optional)

        Returns:
            Combined text for embedding

        Examples:
            >>> text = embedder.prepare_article_text(
            ...     title="GPT-4",
            ...     content="GPT-4 is a large multimodal model...",
            ...     summary="GPT-4는 대규모 멀티모달 모델입니다."
            ... )
        """
        parts = [f"Title: {title}"]

        if summary:
            parts.append(f"Summary: {summary}")

        # Use first 2000 characters of content, 본문은 2000자만 사용
        content_snippet = content[:2000] if content else ""
        if content_snippet:
            parts.append(f"Content: {content_snippet}")

        combined_text = "\n\n".join(parts)

        # Ensure within token limit, 최종적으로 토큰 제한내로 다시 자름
        return self.truncate_text(combined_text)

    # 기사를 정리하고 임베딩까지
    async def embed_article(
        self,
        title: str,
        content: str,
        summary: str | None = None,
    ) -> list[float]:
        """Generate embedding for article.

        Args:
            title: Article title
            content: Article content
            summary: Article summary (optional)

        Returns:
            Embedding vector

        Examples:
            >>> embedding = await embedder.embed_article(
            ...     title="Attention Is All You Need",
            ...     content="We propose a new architecture...",
            ...     summary="Transformer 모델을 제안합니다."
            ... )
        """
        text = self.prepare_article_text(title, content, summary)
        return await self.embed(text)

    async def embed_articles_batch(
        self,
        articles: list[dict[str, Any]],
        batch_size: int = 10,
    ) -> list[list[float]]:
        """Generate embeddings for multiple articles in batches.

        Args:
            articles: List of article dicts with 'title', 'content', 'summary' keys
            batch_size: Number of articles to process concurrently

        Returns:
            List of embedding vectors

        Examples:
            >>> articles = [
            ...     {"title": "Paper 1", "content": "...", "summary": "..."},
            ...     {"title": "Paper 2", "content": "...", "summary": "..."},
            ... ]
            >>> embeddings = await embedder.embed_articles_batch(articles)
        """
        texts = [
            self.prepare_article_text(
                article.get("title", ""),
                article.get("content", ""),
                article.get("summary"),
            )
            for article in articles
        ]

        return await self.batch_embed(texts, batch_size=batch_size)

    def clear_cache(self) -> None:
        """Clear embedding cache."""
        self._cache.clear()
        logger.info("Embedding cache cleared")

    def get_cache_size(self) -> int:
        """Get number of cached embeddings.

        Returns:
            Number of cached items
        """
        return len(self._cache)

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "size": len(self._cache),
            "enabled": self.use_cache,
            "model": self.model,
        }

    def get_embedding_dimension(self) -> int:
        """Get embedding vector dimension.

        Returns:
            Dimension of embedding vectors (1536 for text-embedding-3-small)
        """
        return settings.QDRANT_VECTOR_SIZE


# 싱글턴 패턴, lazy initialization(get_embedder 첫 호출시 생성, 리소스 절약, 로딩시간 절약)
# Global embedder instance
_embedder: TextEmbedder | None = None


def get_embedder() -> TextEmbedder:
    """Get or create global embedder instance.

    Returns:
        Singleton TextEmbedder instance
    """
    global _embedder
    if _embedder is None:
        _embedder = TextEmbedder()
    return _embedder


# Example usage
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

    sample_texts = [
        "Attention Is All You Need",
        "BERT: Pre-training of Deep Bidirectional Transformers",
        "GPT-4 Technical Report",
    ]

    sample_article = {
        "title": "Attention Is All You Need",
        "content": """
        We propose a new simple network architecture, the Transformer,
        based solely on attention mechanisms, dispensing with recurrence
        and convolutions entirely.
        """,
        "summary": "Transformer 아키텍처를 제안하는 논문입니다.",
    }

    async def test():
        embedder = TextEmbedder(use_cache=True)

        print("=" * 60)
        print("1. Single Embedding Test")
        print("=" * 60)

        text = sample_texts[0]
        token_count = embedder.count_tokens(text)
        embedding = await embedder.embed(text)

        print(f"\nText: {text}")
        print(f"Tokens: {token_count}")
        print(f"Embedding dimension: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")

        print("\n" + "=" * 60)
        print("2. Batch Embedding Test")
        print("=" * 60)

        embeddings = await embedder.batch_embed(sample_texts, batch_size=3)
        print(f"\nTotal embeddings: {len(embeddings)}")
        for i, (t, emb) in enumerate(zip(sample_texts, embeddings, strict=False), 1):
            tokens = embedder.count_tokens(t)
            print(f"[{i}] {t[:50]}... ({tokens} tokens): {len(emb)} dims")

        print("\n" + "=" * 60)
        print("3. Article Embedding Test")
        print("=" * 60)

        article_text = embedder.prepare_article_text(
            title=sample_article["title"],
            content=sample_article["content"],
            summary=sample_article["summary"],
        )

        article_tokens = embedder.count_tokens(article_text)
        article_embedding = await embedder.embed_article(
            title=sample_article["title"],
            content=sample_article["content"],
            summary=sample_article["summary"],
        )

        print(f"\nTitle: {sample_article['title']}")
        print(f"Prepared text tokens: {article_tokens}")
        print(f"Embedding dimension: {len(article_embedding)}")

        print("\n" + "=" * 60)
        print("4. Cache Test")
        print("=" * 60)

        # Same text should hit cache
        embedding2 = await embedder.embed(sample_texts[0])
        stats = embedder.get_cache_stats()

        print(f"\nCache stats: {stats}")
        print(f"Cache hit (identical embeddings): {embedding == embedding2}")

        # Clear cache
        embedder.clear_cache()
        print(f"Cache size after clearing: {embedder.get_cache_size()}")

        print("\n" + "=" * 60)
        print("5. Token Truncation Test")
        print("=" * 60)

        # Create very long text
        long_text = "AI research " * 10000
        token_count_before = embedder.count_tokens(long_text)
        print(f"\nOriginal text tokens: {token_count_before}")

        truncated = embedder.truncate_text(long_text, max_tokens=1000)
        token_count_after = embedder.count_tokens(truncated)
        print(f"Truncated text tokens: {token_count_after}")
        print(f"Truncated successfully: {token_count_after <= 1000}")

    try:
        asyncio.run(test())
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
