"""
텍스트 임베딩 생성기

OpenAI Embedding API를 사용하여 텍스트를 벡터로 변환합니다.
Vector DB 저장 및 시맨틱 검색에 사용됩니다.
"""

import asyncio
import hashlib
import logging

from ..llm.client import get_llm_client

logger = logging.getLogger(__name__)


class TextEmbedder:
    """텍스트 임베딩 생성 클래스"""

    def __init__(
        self,
        model: str | None = None,
        use_cache: bool = True,
    ):
        """
        Args:
            model: 임베딩 모델 (None이면 기본 모델 사용)
            use_cache: 캐싱 사용 여부 (동일 텍스트 재사용)
        """
        self.model = model
        self.use_cache = use_cache
        self.llm_client = get_llm_client(provider="openai", model=model)

        # 캐시 (메모리)
        self._cache: dict[str, list[float]] = {}

    def _get_cache_key(self, text: str) -> str:
        """텍스트의 캐시 키 생성 (SHA-256 해시)"""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    async def embed(self, text: str) -> list[float]:
        """
        단일 텍스트 임베딩 생성

        Args:
            text: 임베딩할 텍스트

        Returns:
            임베딩 벡터 (리스트)

        Examples:
            >>> embedder = TextEmbedder()
            >>> embedding = await embedder.embed("Attention Is All You Need")
            >>> print(len(embedding))  # 1536 (OpenAI text-embedding-3-small)
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            # 빈 벡터 반환 (차원은 모델 기본 차원)
            return [0.0] * 1536

        # 캐시 확인
        if self.use_cache:
            cache_key = self._get_cache_key(text)
            if cache_key in self._cache:
                logger.debug(f"Cache hit for text: {text[:50]}...")
                return self._cache[cache_key]

        try:
            # LLM Client를 통한 임베딩 생성
            embedding = await self.llm_client.agenerate_embedding(text)

            # 캐시 저장
            if self.use_cache:
                cache_key = self._get_cache_key(text)
                self._cache[cache_key] = embedding

            logger.info(f"Embedding generated: {len(embedding)} dimensions " f"for text: {text[:50]}...")

            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def batch_embed(
        self,
        texts: list[str],
        batch_size: int = 100,
    ) -> list[list[float]]:
        """
        여러 텍스트 동시 임베딩 (병렬 처리)

        Args:
            texts: 텍스트 리스트
            batch_size: 배치 크기 (OpenAI API는 배치 지원하지만 여기서는 병렬 처리)

        Returns:
            임베딩 벡터 리스트

        Examples:
            >>> texts = ["Text 1", "Text 2", "Text 3"]
            >>> embeddings = await embedder.batch_embed(texts)
            >>> print(len(embeddings))  # 3
        """
        if not texts:
            logger.warning("Empty texts list provided")
            return []

        try:
            # 병렬 처리 (asyncio.gather 사용)
            embeddings = await asyncio.gather(
                *[self.embed(text) for text in texts],
                return_exceptions=True,
            )

            # 에러 처리
            processed_embeddings = []
            for i, embedding in enumerate(embeddings):
                if isinstance(embedding, Exception):
                    logger.error(f"Error embedding text {i}: {embedding}")
                    # 빈 벡터로 대체
                    processed_embeddings.append([0.0] * 1536)
                else:
                    processed_embeddings.append(embedding)

            logger.info(
                f"Batch embedding completed: "
                f"{len(processed_embeddings)} texts, "
                f"{sum(1 for e in embeddings if not isinstance(e, Exception))} succeeded",
            )

            return processed_embeddings

        except Exception as e:
            logger.error(f"Error in batch embedding: {e}")
            raise

    def embed_article(self, title: str, content: str, summary: str | None = None) -> str:
        """
        아티클을 임베딩하기 위한 텍스트 생성

        제목, 요약(있으면), 내용을 결합하여 최적의 임베딩 텍스트 생성

        Args:
            title: 제목
            content: 내용
            summary: 요약 (선택적)

        Returns:
            임베딩할 텍스트

        Examples:
            >>> text = embedder.embed_article(
            ...     title="GPT-4",
            ...     content="GPT-4 is a large multimodal model...",
            ...     summary="GPT-4는 대규모 멀티모달 모델입니다."
            ... )
        """
        parts = [f"제목: {title}"]

        if summary:
            parts.append(f"요약: {summary}")

        # 내용은 처음 1000자만 사용 (임베딩 토큰 제한 고려)
        content_snippet = content[:1000]
        parts.append(f"내용: {content_snippet}")

        return "\n\n".join(parts)

    async def embed_article_async(
        self,
        title: str,
        content: str,
        summary: str | None = None,
    ) -> list[float]:
        """
        아티클 임베딩 생성 (비동기)

        Args:
            title: 제목
            content: 내용
            summary: 요약

        Returns:
            임베딩 벡터
        """
        text = self.embed_article(title, content, summary)
        return await self.embed(text)

    def clear_cache(self) -> None:
        """캐시 초기화"""
        self._cache.clear()
        logger.info("Cache cleared")

    def get_cache_size(self) -> int:
        """캐시 크기 반환"""
        return len(self._cache)

    def get_embedding_dimension(self) -> int:
        """임베딩 차원 반환"""
        # OpenAI text-embedding-3-small: 1536
        # 추후 모델에 따라 동적으로 변경 가능
        return 1536


# 사용 예시
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

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
        print("단일 임베딩 테스트")
        print("=" * 60)

        embedding = await embedder.embed(sample_texts[0])
        print(f"\n텍스트: {sample_texts[0]}")
        print(f"임베딩 차원: {len(embedding)}")
        print(f"첫 5개 값: {embedding[:5]}")

        print("\n" + "=" * 60)
        print("배치 임베딩 테스트")
        print("=" * 60)

        embeddings = await embedder.batch_embed(sample_texts)
        print(f"\n임베딩 개수: {len(embeddings)}")
        for i, (text, emb) in enumerate(zip(sample_texts, embeddings, strict=False), 1):
            print(f"[{i}] {text[:50]}: {len(emb)} dims")

        print("\n" + "=" * 60)
        print("아티클 임베딩 테스트")
        print("=" * 60)

        article_embedding = await embedder.embed_article_async(
            title=sample_article["title"],
            content=sample_article["content"],
            summary=sample_article["summary"],
        )

        print(f"\n제목: {sample_article['title']}")
        print(f"임베딩 차원: {len(article_embedding)}")

        print("\n" + "=" * 60)
        print("캐시 테스트")
        print("=" * 60)

        # 같은 텍스트 다시 임베딩 (캐시 히트)
        embedding2 = await embedder.embed(sample_texts[0])
        print(f"\n캐시 크기: {embedder.get_cache_size()}")
        print(f"캐시된 임베딩 동일: {embedding == embedding2}")

        # 캐시 초기화
        embedder.clear_cache()
        print(f"캐시 초기화 후 크기: {embedder.get_cache_size()}")

    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        print("\n테스트 중단됨")
    except Exception as e:
        print(f"\n에러 발생: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
