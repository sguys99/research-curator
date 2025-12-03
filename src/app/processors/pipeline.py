"""
통합 처리 파이프라인

모든 프로세서를 결합하여 아티클을 자동으로 처리합니다.
수집 → 요약 → 평가 → 분류 → 임베딩
"""

import asyncio
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any

from .classifier import ContentClassifier
from .embedder import TextEmbedder
from .evaluator import ImportanceEvaluator
from .summarizer import ArticleSummarizer

logger = logging.getLogger(__name__)


@dataclass
class ProcessedArticle:
    """처리된 아티클 데이터 클래스"""

    # 원본 데이터
    title: str
    content: str
    url: str
    source_name: str
    source_type: str

    # 처리 결과
    summary: str
    importance_score: float
    category: str
    keywords: list[str]
    research_field: str
    embedding: list[float]

    # 상세 평가
    innovation_score: float
    relevance_score: float
    impact_score: float
    timeliness_score: float

    # 메타데이터
    metadata: dict[str, Any] = field(default_factory=dict)
    processed_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        data["processed_at"] = self.processed_at.isoformat()
        return data


class ProcessingPipeline:
    """통합 처리 파이프라인"""

    def __init__(
        self,
        provider: str = "openai",
        model: str | None = None,
        summary_length: str = "medium",
        summary_language: str = "ko",
        use_embedding_cache: bool = True,
    ):
        """
        Args:
            provider: LLM 프로바이더 ("openai" 또는 "claude")
            model: 사용할 모델 (None이면 기본 모델)
            summary_length: 요약 길이 ("short", "medium", "long")
            summary_language: 요약 언어 ("ko", "en")
            use_embedding_cache: 임베딩 캐싱 사용 여부
        """
        self.provider = provider
        self.model = model
        self.summary_length = summary_length
        self.summary_language = summary_language

        # 프로세서 초기화
        self.summarizer = ArticleSummarizer(provider=provider, model=model)
        self.evaluator = ImportanceEvaluator(provider=provider, model=model)
        self.classifier = ContentClassifier(provider=provider, model=model)
        self.embedder = TextEmbedder(use_cache=use_embedding_cache)

    async def process_article(
        self,
        title: str,
        content: str,
        url: str = "",
        source_name: str = "",
        source_type: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> ProcessedArticle:
        """
        단일 아티클 전체 처리

        처리 순서:
        1. 요약, 평가, 분류 병렬 실행 (가장 느린 단계)
        2. 임베딩 생성 (요약 사용)

        Args:
            title: 제목
            content: 내용
            url: 원문 URL
            source_name: 소스 이름
            source_type: 소스 타입
            metadata: 메타데이터

        Returns:
            ProcessedArticle 객체

        Examples:
            >>> pipeline = ProcessingPipeline()
            >>> result = await pipeline.process_article(
            ...     title="Attention Is All You Need",
            ...     content="We propose the Transformer...",
            ...     url="https://arxiv.org/abs/1706.03762",
            ...     source_name="arXiv",
            ...     metadata={"year": 2017, "citations": 50000}
            ... )
        """
        start_time = datetime.now()
        metadata = metadata or {}

        try:
            # Step 1: 요약, 평가, 분류 병렬 실행
            logger.info(f"Processing article: {title[:50]}...")

            summary_task = self.summarizer.summarize(
                title=title,
                content=content,
                language=self.summary_language,
                length=self.summary_length,
            )

            eval_task = self.evaluator.evaluate(title=title, content=content, metadata=metadata)

            classify_task = self.classifier.classify(
                title=title,
                content=content,
                source_name=source_name,
                url=url,
            )

            # 병렬 실행
            summary, eval_result, class_result = await asyncio.gather(
                summary_task,
                eval_task,
                classify_task,
            )

            # Step 2: 임베딩 생성 (요약 사용)
            embedding = await self.embedder.embed_article_async(
                title=title,
                content=content,
                summary=summary,
            )

            # 결과 객체 생성
            processed = ProcessedArticle(
                # 원본
                title=title,
                content=content,
                url=url,
                source_name=source_name,
                source_type=source_type,
                # 처리 결과
                summary=summary,
                importance_score=eval_result["final_score"],
                category=class_result["category"],
                keywords=class_result.get("keywords", []),
                research_field=class_result.get("research_field", "Other"),
                embedding=embedding,
                # 상세 평가
                innovation_score=eval_result["innovation"],
                relevance_score=eval_result["relevance"],
                impact_score=eval_result["impact"],
                timeliness_score=eval_result["timeliness"],
                # 메타데이터
                metadata=metadata,
            )

            elapsed = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Article processed in {elapsed:.2f}s: "
                f"{title[:50]}... (score={processed.importance_score:.2f})",
            )

            return processed

        except Exception as e:
            logger.error(f"Error processing article '{title[:50]}...': {e}")
            raise

    async def process_batch(
        self,
        articles: list[dict[str, Any]],
        max_concurrent: int = 5,
    ) -> list[ProcessedArticle]:
        """
        여러 아티클 배치 처리

        최적화 전략:
        1. 각 아티클 내에서 요약/평가/분류 병렬 실행
        2. 여러 아티클 동시 처리 (max_concurrent 제한)

        Args:
            articles: 아티클 리스트
                [{"title": "...", "content": "...", "url": "...", ...}, ...]
            max_concurrent: 최대 동시 처리 개수

        Returns:
            ProcessedArticle 리스트

        Examples:
            >>> articles = [
            ...     {"title": "Paper 1", "content": "...", "url": "..."},
            ...     {"title": "Paper 2", "content": "...", "url": "..."},
            ... ]
            >>> results = await pipeline.process_batch(articles)
        """
        start_time = datetime.now()
        total = len(articles)

        logger.info(f"Processing batch of {total} articles...")

        # 세마포어로 동시 실행 제한
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(article: dict[str, Any]) -> ProcessedArticle:
            async with semaphore:
                return await self.process_article(
                    title=article["title"],
                    content=article["content"],
                    url=article.get("url", ""),
                    source_name=article.get("source_name", ""),
                    source_type=article.get("source_type", ""),
                    metadata=article.get("metadata"),
                )

        # 병렬 처리
        results = await asyncio.gather(
            *[process_with_semaphore(article) for article in articles],
            return_exceptions=True,
        )

        # 에러 처리
        processed_articles = []
        errors = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing article {i}: {result}")
                errors += 1
            else:
                processed_articles.append(result)

        elapsed = (datetime.now() - start_time).total_seconds()
        success_rate = (total - errors) / total * 100 if total > 0 else 0

        logger.info(
            f"Batch processing completed in {elapsed:.2f}s: "
            f"{total} articles, {len(processed_articles)} succeeded ({success_rate:.1f}%), "
            f"{errors} failed",
        )

        return processed_articles

    def get_top_articles(
        self,
        processed_articles: list[ProcessedArticle],
        top_n: int = 5,
    ) -> list[ProcessedArticle]:
        """
        중요도 순으로 상위 N개 아티클 반환

        Args:
            processed_articles: 처리된 아티클 리스트
            top_n: 반환할 개수

        Returns:
            중요도 순으로 정렬된 상위 N개 아티클
        """
        sorted_articles = sorted(processed_articles, key=lambda x: x.importance_score, reverse=True)
        return sorted_articles[:top_n]

    def filter_by_category(
        self,
        processed_articles: list[ProcessedArticle],
        category: str,
    ) -> list[ProcessedArticle]:
        """카테고리별 필터링"""
        return [a for a in processed_articles if a.category == category]

    def filter_by_score(
        self,
        processed_articles: list[ProcessedArticle],
        min_score: float,
    ) -> list[ProcessedArticle]:
        """최소 점수 이상만 필터링"""
        return [a for a in processed_articles if a.importance_score >= min_score]

    def get_statistics(self, processed_articles: list[ProcessedArticle]) -> dict[str, Any]:
        """처리 결과 통계"""
        if not processed_articles:
            return {}

        # 카테고리 분포
        category_dist = {}
        for article in processed_articles:
            cat = article.category
            category_dist[cat] = category_dist.get(cat, 0) + 1

        # 점수 통계
        scores = [a.importance_score for a in processed_articles]

        return {
            "total": len(processed_articles),
            "category_distribution": category_dist,
            "average_score": sum(scores) / len(scores),
            "max_score": max(scores),
            "min_score": min(scores),
            "high_quality_count": len([s for s in scores if s >= 0.7]),
        }


# 사용 예시
if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)

    # 샘플 아티클
    sample_articles = [
        {
            "title": "Attention Is All You Need",
            "content": """
            We propose a new simple network architecture, the Transformer,
            based solely on attention mechanisms, dispensing with recurrence
            and convolutions entirely.
            """,
            "url": "https://arxiv.org/abs/1706.03762",
            "source_name": "arXiv",
            "metadata": {"year": 2017, "citations": 50000},
        },
        {
            "title": "GPT-4 Technical Report",
            "content": "GPT-4 is a large multimodal model capable of processing...",
            "url": "https://openai.com/research/gpt-4",
            "source_name": "OpenAI",
            "metadata": {"year": 2023, "citations": 5000},
        },
        {
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "content": "We introduce BERT, a new language representation model...",
            "url": "https://arxiv.org/abs/1810.04805",
            "source_name": "arXiv",
            "metadata": {"year": 2018, "citations": 30000},
        },
    ]

    async def test():
        pipeline = ProcessingPipeline(provider="openai", summary_length="medium")

        print("=" * 60)
        print("단일 아티클 처리 테스트")
        print("=" * 60)

        result = await pipeline.process_article(
            title=sample_articles[0]["title"],
            content=sample_articles[0]["content"],
            url=sample_articles[0]["url"],
            source_name=sample_articles[0]["source_name"],
            metadata=sample_articles[0]["metadata"],
        )

        print(f"\n제목: {result.title}")
        print(f"요약: {result.summary[:100]}...")
        print(f"중요도: {result.importance_score:.2f}")
        print(f"카테고리: {result.category}")
        print(f"키워드: {', '.join(result.keywords[:5])}")
        print(f"임베딩: {len(result.embedding)} dimensions")

        print("\n" + "=" * 60)
        print("배치 처리 테스트 (3개)")
        print("=" * 60)

        results = await pipeline.process_batch(sample_articles, max_concurrent=2)

        print(f"\n처리 완료: {len(results)}개")
        for i, article in enumerate(results, 1):
            print(
                f"  [{i}] {article.title[:40]}... → "
                f"{article.importance_score:.2f} ({article.category})",
            )

        # 상위 아티클
        print("\n" + "=" * 60)
        print("상위 2개 아티클")
        print("=" * 60)

        top_articles = pipeline.get_top_articles(results, top_n=2)
        for i, article in enumerate(top_articles, 1):
            print(f"  [{i}] {article.title} - {article.importance_score:.2f}")

        # 통계
        print("\n" + "=" * 60)
        print("처리 통계")
        print("=" * 60)

        stats = pipeline.get_statistics(results)
        print(f"  총 개수: {stats['total']}")
        print(f"  평균 점수: {stats['average_score']:.2f}")
        print(f"  카테고리 분포: {stats['category_distribution']}")
        print(f"  고품질 (≥0.7): {stats['high_quality_count']}")

    try:
        asyncio.run(test())
    except KeyboardInterrupt:
        print("\n테스트 중단됨")
    except Exception as e:
        print(f"\n에러 발생: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
