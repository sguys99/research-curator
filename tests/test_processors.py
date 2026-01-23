"""Unit tests for processors."""

import pytest

from app.processors import ArticleSummarizer, ContentClassifier, ImportanceEvaluator, TextEmbedder


@pytest.mark.unit
@pytest.mark.asyncio
async def test_summarizer(sample_article, llm_mock):
    summarizer = ArticleSummarizer(provider="openai")

    summary = await summarizer.summarize(
        title=sample_article["title"],
        content=sample_article["content"],
        language="ko",
        length="medium",
    )

    assert isinstance(summary, str)
    assert summary


@pytest.mark.unit
@pytest.mark.asyncio
async def test_evaluator(sample_article, llm_mock):
    evaluator = ImportanceEvaluator(provider="openai")

    result = await evaluator.evaluate(
        title=sample_article["title"],
        content=sample_article["content"],
        metadata=sample_article["metadata"],
    )

    assert isinstance(result, dict)
    assert 0.0 <= result["final_score"] <= 1.0
    assert 0.0 <= result["innovation"] <= 1.0
    assert 0.0 <= result["relevance"] <= 1.0
    assert 0.0 <= result["impact"] <= 1.0
    assert 0.0 <= result["timeliness"] <= 1.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_classifier(sample_article, llm_mock):
    classifier = ContentClassifier(provider="openai")

    result = await classifier.classify(
        title=sample_article["title"],
        content=sample_article["content"],
        source_name=sample_article["source_name"],
        url=sample_article["url"],
    )

    assert isinstance(result, dict)
    assert result["category"] in ["paper", "news", "report", "blog", "other"]
    assert result["category"] == "paper"
    assert 0.0 <= result["confidence"] <= 1.0


@pytest.mark.unit
@pytest.mark.asyncio
async def test_embedder(sample_article, llm_mock):
    embedder = TextEmbedder()

    embedding = await embedder.embed(sample_article["title"])

    assert isinstance(embedding, list)
    assert len(embedding) == embedder.get_embedding_dimension()
    assert all(isinstance(x, float) for x in embedding)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_all_processors_flow(sample_article, llm_mock):
    summarizer = ArticleSummarizer(provider="openai")
    summary = await summarizer.summarize(
        title=sample_article["title"],
        content=sample_article["content"],
        language="ko",
        length="medium",
    )
    assert summary

    evaluator = ImportanceEvaluator(provider="openai")
    eval_result = await evaluator.evaluate(
        title=sample_article["title"],
        content=sample_article["content"],
        metadata=sample_article["metadata"],
    )
    assert 0.0 <= eval_result["final_score"] <= 1.0

    classifier = ContentClassifier(provider="openai")
    class_result = await classifier.classify(
        title=sample_article["title"],
        content=sample_article["content"],
        source_name=sample_article["source_name"],
        url=sample_article["url"],
    )
    assert class_result["category"] == "paper"

    embedder = TextEmbedder()
    embedding = await embedder.embed_article_async(
        title=sample_article["title"],
        content=sample_article["content"],
        summary=summary,
    )
    assert len(embedding) == embedder.get_embedding_dimension()
