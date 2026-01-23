"""Unit tests for the processing pipeline."""

import pytest

from app.processors import ProcessingPipeline


@pytest.mark.unit
@pytest.mark.asyncio
async def test_single_article_processing(sample_article, llm_mock):
    pipeline = ProcessingPipeline(provider="openai", summary_length="medium")

    result = await pipeline.process_article(
        title=sample_article["title"],
        content=sample_article["content"],
        url=sample_article["url"],
        source_name=sample_article["source_name"],
        metadata=sample_article["metadata"],
    )

    assert result.title == sample_article["title"]
    assert result.summary
    assert 0.0 <= result.importance_score <= 1.0
    assert result.category in ["paper", "news", "report", "blog", "other"]
    assert len(result.embedding) == 1536


@pytest.mark.unit
@pytest.mark.asyncio
async def test_batch_processing(sample_articles, llm_mock):
    pipeline = ProcessingPipeline(provider="openai", summary_length="short")

    results = await pipeline.process_batch(sample_articles, max_concurrent=2)

    assert len(results) == len(sample_articles)
    assert all(r.summary for r in results)
    assert all(0.0 <= r.importance_score <= 1.0 for r in results)
    assert all(len(r.embedding) == 1536 for r in results)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_pipeline_utilities(sample_articles, llm_mock):
    pipeline = ProcessingPipeline(provider="openai")

    results = await pipeline.process_batch(sample_articles[:2])

    top_articles = pipeline.get_top_articles(results, top_n=1)
    assert len(top_articles) == 1
    assert top_articles[0].importance_score >= results[0].importance_score

    filtered = pipeline.filter_by_score(results, min_score=0.5)
    assert all(a.importance_score >= 0.5 for a in filtered)

    stats = pipeline.get_statistics(results)
    assert stats["total"] == 2
    assert "average_score" in stats
    assert "category_distribution" in stats


@pytest.mark.unit
@pytest.mark.asyncio
async def test_processed_article_to_dict(sample_article, llm_mock):
    pipeline = ProcessingPipeline(provider="openai")

    result = await pipeline.process_article(
        title=sample_article["title"],
        content=sample_article["content"],
        url=sample_article["url"],
        source_name=sample_article["source_name"],
    )

    data = result.to_dict()

    assert isinstance(data, dict)
    assert "title" in data
    assert "summary" in data
    assert "importance_score" in data
    assert "embedding" in data
    assert "processed_at" in data
