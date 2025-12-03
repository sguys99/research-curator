"""
통합 파이프라인 테스트

Checkpoint 3 검증:
- 통합 파이프라인 1개 논문 처리 성공
- 배치 처리 5개 논문 동시 처리 성공
- 처리 시간 < 30초 (5개 기준)
"""

import asyncio
import time

import pytest

from src.app.processors import ProcessingPipeline

# 테스트용 샘플 아티클
SAMPLE_ARTICLES = [
    {
        "title": "Attention Is All You Need",
        "content": "We propose the Transformer, based solely on attention mechanisms...",
        "url": "https://arxiv.org/abs/1706.03762",
        "source_name": "arXiv",
        "metadata": {"year": 2017, "citations": 50000},
    },
    {
        "title": "GPT-4 Technical Report",
        "content": "GPT-4 is a large multimodal model...",
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
    {
        "title": "ResNet: Deep Residual Learning",
        "content": "Deep residual learning framework...",
        "url": "https://arxiv.org/abs/1512.03385",
        "source_name": "arXiv",
        "metadata": {"year": 2015, "citations": 100000},
    },
    {
        "title": "Generative Adversarial Networks",
        "content": "We propose a new framework for estimating generative models...",
        "url": "https://arxiv.org/abs/1406.2661",
        "source_name": "arXiv",
        "metadata": {"year": 2014, "citations": 80000},
    },
]


@pytest.mark.asyncio
async def test_single_article_processing():
    """✅ Checkpoint 3.1: 통합 파이프라인 1개 논문 처리 성공"""
    pipeline = ProcessingPipeline(provider="openai", summary_length="medium")

    start = time.time()
    result = await pipeline.process_article(
        title=SAMPLE_ARTICLES[0]["title"],
        content=SAMPLE_ARTICLES[0]["content"],
        url=SAMPLE_ARTICLES[0]["url"],
        source_name=SAMPLE_ARTICLES[0]["source_name"],
        metadata=SAMPLE_ARTICLES[0]["metadata"],
    )
    elapsed = time.time() - start

    # 검증
    assert result.title == SAMPLE_ARTICLES[0]["title"]
    assert len(result.summary) > 0
    assert 0.0 <= result.importance_score <= 1.0
    assert result.category in ["paper", "news", "report", "blog", "other"]
    assert len(result.embedding) == 1536
    assert elapsed < 30  # 30초 이내

    print(f"✅ 단일 처리 성공 ({elapsed:.2f}초)")
    print(f"   중요도: {result.importance_score:.2f}")
    print(f"   카테고리: {result.category}")


@pytest.mark.asyncio
async def test_batch_processing():
    """✅ Checkpoint 3.2: 배치 처리 5개 논문 동시 처리 성공"""
    pipeline = ProcessingPipeline(provider="openai", summary_length="short")

    start = time.time()
    results = await pipeline.process_batch(SAMPLE_ARTICLES, max_concurrent=3)
    elapsed = time.time() - start

    # 검증
    assert len(results) == 5
    assert all(len(r.summary) > 0 for r in results)
    assert all(0.0 <= r.importance_score <= 1.0 for r in results)
    assert all(len(r.embedding) == 1536 for r in results)
    assert elapsed < 30  # 30초 이내

    print(f"✅ 배치 처리 성공 ({elapsed:.2f}초)")
    print(f"   평균 처리 시간: {elapsed/len(results):.2f}초/아티클")


@pytest.mark.asyncio
async def test_pipeline_utilities():
    """파이프라인 유틸리티 함수 테스트"""
    pipeline = ProcessingPipeline(provider="openai")

    # 2개만 처리
    results = await pipeline.process_batch(SAMPLE_ARTICLES[:2])

    # 상위 아티클
    top_articles = pipeline.get_top_articles(results, top_n=1)
    assert len(top_articles) == 1
    assert top_articles[0].importance_score >= results[0].importance_score

    # 점수 필터링
    filtered = pipeline.filter_by_score(results, min_score=0.5)
    assert all(a.importance_score >= 0.5 for a in filtered)

    # 통계
    stats = pipeline.get_statistics(results)
    assert stats["total"] == 2
    assert "average_score" in stats
    assert "category_distribution" in stats

    print("✅ 유틸리티 함수 테스트 성공")


@pytest.mark.asyncio
async def test_processed_article_to_dict():
    """ProcessedArticle to_dict 테스트"""
    pipeline = ProcessingPipeline(provider="openai")

    result = await pipeline.process_article(
        title=SAMPLE_ARTICLES[0]["title"],
        content=SAMPLE_ARTICLES[0]["content"],
        url=SAMPLE_ARTICLES[0]["url"],
        source_name=SAMPLE_ARTICLES[0]["source_name"],
    )

    # 딕셔너리 변환
    data = result.to_dict()

    assert isinstance(data, dict)
    assert "title" in data
    assert "summary" in data
    assert "importance_score" in data
    assert "embedding" in data
    assert "processed_at" in data

    print("✅ to_dict 변환 성공")


if __name__ == "__main__":
    # pytest 대신 직접 실행
    async def run_all():
        print("=" * 60)
        print("통합 파이프라인 테스트")
        print("=" * 60)

        await test_single_article_processing()
        await test_batch_processing()
        await test_pipeline_utilities()
        await test_processed_article_to_dict()

        print("\n" + "=" * 60)
        print("✅ 모든 테스트 통과!")
        print("=" * 60)

    asyncio.run(run_all())
