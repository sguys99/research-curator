"""
Processors 통합 테스트

Checkpoint 2 검증:
- 단일 논문 요약 생성 성공
- 중요도 점수 0.0-1.0 범위 내 반환
- 카테고리 정확히 분류
- 임베딩 벡터 생성 성공
"""

import asyncio

import pytest

from src.app.processors import (
    ArticleSummarizer,
    ContentClassifier,
    ImportanceEvaluator,
    TextEmbedder,
)

# 테스트용 샘플 아티클
SAMPLE_ARTICLE = {
    "title": "Attention Is All You Need",
    "content": """
    We propose a new simple network architecture, the Transformer,
    based solely on attention mechanisms, dispensing with recurrence
    and convolutions entirely. Experiments on two machine translation
    tasks show these models to be superior in quality while being
    more parallelizable and requiring significantly less time to train.
    """,
    "source_name": "arXiv",
    "url": "https://arxiv.org/abs/1706.03762",
    "metadata": {"citations": 50000, "year": 2017},
}


@pytest.mark.asyncio
async def test_summarizer():
    """✅ Checkpoint 2.1: 단일 논문 요약 생성 성공"""
    summarizer = ArticleSummarizer(provider="openai")

    summary = await summarizer.summarize(
        title=SAMPLE_ARTICLE["title"],
        content=SAMPLE_ARTICLE["content"],
        language="ko",
        length="medium",
    )

    # 검증
    assert isinstance(summary, str)
    assert len(summary) > 0
    assert len(summary) > 50  # 최소 길이 확인
    print(f"✅ 요약 생성 성공: {summary[:100]}...")


@pytest.mark.asyncio
async def test_evaluator():
    """✅ Checkpoint 2.2: 중요도 점수 0.0-1.0 범위 내 반환"""
    evaluator = ImportanceEvaluator(provider="openai")

    result = await evaluator.evaluate(
        title=SAMPLE_ARTICLE["title"],
        content=SAMPLE_ARTICLE["content"],
        metadata=SAMPLE_ARTICLE["metadata"],
    )

    # 검증
    assert isinstance(result, dict)
    assert "final_score" in result

    # 점수 범위 확인
    assert 0.0 <= result["final_score"] <= 1.0
    assert 0.0 <= result["innovation"] <= 1.0
    assert 0.0 <= result["relevance"] <= 1.0
    assert 0.0 <= result["impact"] <= 1.0
    assert 0.0 <= result["timeliness"] <= 1.0

    print(f"✅ 중요도 평가 성공: final_score={result['final_score']:.2f}")


@pytest.mark.asyncio
async def test_classifier():
    """✅ Checkpoint 2.3: 카테고리 정확히 분류"""
    classifier = ContentClassifier(provider="openai")

    result = await classifier.classify(
        title=SAMPLE_ARTICLE["title"],
        content=SAMPLE_ARTICLE["content"],
        source_name=SAMPLE_ARTICLE["source_name"],
        url=SAMPLE_ARTICLE["url"],
    )

    # 검증
    assert isinstance(result, dict)
    assert "category" in result
    assert result["category"] in ["paper", "news", "report", "blog", "other"]

    # arXiv 논문이므로 "paper"로 분류되어야 함
    assert result["category"] == "paper"
    assert 0.0 <= result["confidence"] <= 1.0

    print(f"✅ 카테고리 분류 성공: {result['category']} " f"(신뢰도: {result['confidence']:.2f})")


@pytest.mark.asyncio
async def test_embedder():
    """✅ Checkpoint 2.4: 임베딩 벡터 생성 성공"""
    embedder = TextEmbedder()

    embedding = await embedder.embed(SAMPLE_ARTICLE["title"])

    # 검증
    assert isinstance(embedding, list)
    assert len(embedding) > 0
    assert len(embedding) == embedder.get_embedding_dimension()  # 1536
    assert all(isinstance(x, float) for x in embedding)

    print(f"✅ 임베딩 생성 성공: {len(embedding)} dimensions")


@pytest.mark.asyncio
async def test_all_processors_integration():
    """✅ Checkpoint 2 통합 테스트: 모든 프로세서 순차 실행"""
    print("\n" + "=" * 60)
    print("Checkpoint 2 통합 검증")
    print("=" * 60)

    # 1. 요약 생성
    print("\n1️⃣ 요약 생성...")
    summarizer = ArticleSummarizer(provider="openai")
    summary = await summarizer.summarize(
        title=SAMPLE_ARTICLE["title"],
        content=SAMPLE_ARTICLE["content"],
        language="ko",
        length="medium",
    )
    assert len(summary) > 0
    print(f"   ✅ 요약: {summary[:80]}...")

    # 2. 중요도 평가
    print("\n2️⃣ 중요도 평가...")
    evaluator = ImportanceEvaluator(provider="openai")
    eval_result = await evaluator.evaluate(
        title=SAMPLE_ARTICLE["title"],
        content=SAMPLE_ARTICLE["content"],
        metadata=SAMPLE_ARTICLE["metadata"],
    )
    assert 0.0 <= eval_result["final_score"] <= 1.0
    print(f"   ✅ 최종 점수: {eval_result['final_score']:.2f}")

    # 3. 카테고리 분류
    print("\n3️⃣ 카테고리 분류...")
    classifier = ContentClassifier(provider="openai")
    class_result = await classifier.classify(
        title=SAMPLE_ARTICLE["title"],
        content=SAMPLE_ARTICLE["content"],
        source_name=SAMPLE_ARTICLE["source_name"],
        url=SAMPLE_ARTICLE["url"],
    )
    assert class_result["category"] == "paper"
    print(f"   ✅ 카테고리: {class_result['category']}")

    # 4. 임베딩 생성
    print("\n4️⃣ 임베딩 생성...")
    embedder = TextEmbedder()
    embedding = await embedder.embed_article_async(
        title=SAMPLE_ARTICLE["title"],
        content=SAMPLE_ARTICLE["content"],
        summary=summary,
    )
    assert len(embedding) == 1536
    print(f"   ✅ 임베딩: {len(embedding)} dimensions")

    print("\n" + "=" * 60)
    print("✅ Checkpoint 2 통과!")
    print("=" * 60)


if __name__ == "__main__":
    # pytest 대신 직접 실행
    asyncio.run(test_all_processors_integration())
