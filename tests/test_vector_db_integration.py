"""Integration tests for vector DB operations (requires Qdrant + LLM)."""

import pytest

from app.processors.embedder import TextEmbedder, get_embedder
from app.vector_db import (
    CollectionSchema,
    VectorOperations,
    get_qdrant_client,
    get_vector_operations,
    initialize_vector_db,
    verify_collection_schema,
)


@pytest.mark.integration
def test_qdrant_client_and_collection(skip_if_no_qdrant):
    client = get_qdrant_client()
    health = client.health_check()

    assert health["status"] == "healthy"

    schema_info = CollectionSchema.get_schema_info()
    assert schema_info["collection_name"]
    assert schema_info["vector_size"] > 0

    success = initialize_vector_db(recreate=True)
    assert success

    verification = verify_collection_schema(client)
    assert verification["exists"]
    assert verification["schema_valid"]
    assert not verification["errors"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_embedding_pipeline(skip_if_no_qdrant):
    embedder = TextEmbedder(use_cache=True)

    short_text = "Attention Is All You Need"
    long_text = "AI research " * 10000

    short_tokens = embedder.count_tokens(short_text)
    long_tokens = embedder.count_tokens(long_text)

    assert short_tokens < 100
    assert long_tokens > 10000

    truncated = embedder.truncate_text(long_text, max_tokens=1000)
    truncated_tokens = embedder.count_tokens(truncated)
    assert truncated_tokens <= 1000

    embedding = await embedder.embed("Transformer architecture for NLP")
    assert len(embedding) == 1536
    assert all(isinstance(x, float) for x in embedding)

    embeddings = await embedder.batch_embed(
        [
            "Attention Is All You Need",
            "BERT: Pre-training of Deep Bidirectional Transformers",
            "GPT-4 Technical Report",
        ],
        batch_size=2,
    )
    assert len(embeddings) == 3
    assert all(len(e) == 1536 for e in embeddings)

    article_embedding = await embedder.embed_article(
        title="Attention Is All You Need",
        content="The Transformer architecture...",
        summary="Transformer 아키텍처를 제안하는 논문입니다.",
    )
    assert len(article_embedding) == 1536

    emb1 = await embedder.embed("Test caching mechanism")
    emb2 = await embedder.embed("Test caching mechanism")
    assert emb1 == emb2
    stats = embedder.get_cache_stats()
    assert stats["size"] >= 1

    embedder.clear_cache()
    stats = embedder.get_cache_stats()
    assert stats["size"] == 0

    embedder1 = get_embedder()
    embedder2 = get_embedder()
    assert embedder1 is embedder2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_vector_crud(skip_if_no_qdrant):
    init_success = initialize_vector_db(recreate=True)
    assert init_success

    ops = VectorOperations()
    assert ops.count_articles() == 0

    article1 = {
        "article_id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Attention Is All You Need",
        "content": "The Transformer architecture...",
        "summary": "Transformer 아키텍처를 제안하는 논문입니다.",
        "source_type": "paper",
        "category": "NLP",
        "importance_score": 0.95,
        "metadata": {"authors": ["Vaswani et al."], "year": 2017},
    }

    vector_id1 = await ops.insert_article(**article1)
    assert vector_id1
    assert ops.count_articles() == 1

    retrieved = ops.get_article(vector_id1)
    assert retrieved
    assert retrieved["title"] == article1["title"]

    articles_batch = [
        {
            "article_id": "223e4567-e89b-12d3-a456-426614174001",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "content": "BERT model...",
            "summary": "BERT 모델을 소개하는 논문입니다.",
            "source_type": "paper",
            "category": "NLP",
            "importance_score": 0.92,
        },
        {
            "article_id": "323e4567-e89b-12d3-a456-426614174002",
            "title": "GPT-4 Technical Report",
            "content": "GPT-4 is a large-scale model...",
            "summary": "GPT-4의 기술 리포트입니다.",
            "source_type": "report",
            "category": "AI",
            "importance_score": 0.98,
        },
    ]

    vector_ids = await ops.insert_articles_batch(articles_batch, batch_size=2)
    assert len(vector_ids) == 2
    assert ops.count_articles() == 3

    all_vector_ids = [vector_id1] + vector_ids
    retrieved_batch = ops.get_articles_batch(all_vector_ids)
    assert len(retrieved_batch) == 3

    update_success = await ops.update_article(
        vector_id=vector_id1,
        importance_score=0.99,
        category="NLP/Transformers",
    )
    assert update_success
    updated = ops.get_article(vector_id1)
    assert updated["importance_score"] == 0.99

    delete_success = ops.delete_article(vector_ids[0])
    assert delete_success
    assert ops.count_articles() == 2

    remaining_ids = [vector_id1, vector_ids[1]]
    batch_delete_success = ops.delete_articles_batch(remaining_ids)
    assert batch_delete_success
    assert ops.count_articles() == 0

    ops1 = get_vector_operations()
    ops2 = get_vector_operations()
    assert ops1 is ops2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_semantic_search(skip_if_no_qdrant):
    init_success = initialize_vector_db(recreate=True)
    assert init_success

    ops = VectorOperations()

    test_articles = [
        {
            "article_id": "uuid-1",
            "title": "Attention Is All You Need",
            "content": "The dominant sequence transduction models are based on complex recurrent or "
            "convolutional neural networks. We propose the Transformer, based solely on attention.",
            "summary": "Transformer 아키텍처를 소개하는 혁신적인 논문입니다.",
            "source_type": "paper",
            "category": "NLP",
            "importance_score": 0.95,
        },
        {
            "article_id": "uuid-2",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "content": "We introduce BERT, a new language representation model.",
            "summary": "BERT 모델을 소개합니다.",
            "source_type": "paper",
            "category": "NLP",
            "importance_score": 0.92,
        },
        {
            "article_id": "uuid-3",
            "title": "GPT-4 Technical Report",
            "content": "GPT-4 is a large-scale, multimodal model.",
            "summary": "GPT-4의 기술적 세부사항을 다룹니다.",
            "source_type": "report",
            "category": "AI",
            "importance_score": 0.98,
        },
    ]

    vector_ids = await ops.insert_articles_batch(test_articles, batch_size=2)
    assert len(vector_ids) == 3

    results1 = await ops.search_similar_articles(
        query="transformer architecture and attention mechanism",
        limit=3,
        score_threshold=0.5,
    )
    assert results1
    assert results1[0]["score"] > 0.5

    results2_high = await ops.search_similar_articles(
        query="natural language processing models",
        limit=10,
        score_threshold=0.85,
    )
    results2_low = await ops.search_similar_articles(
        query="natural language processing models",
        limit=10,
        score_threshold=0.70,
    )
    assert len(results2_low) >= len(results2_high)

    papers_only = await ops.search_similar_articles(
        query="artificial intelligence research",
        limit=5,
        source_type=["paper"],
    )
    assert all(r["source_type"] == "paper" for r in papers_only)

    reports_only = await ops.search_similar_articles(
        query="artificial intelligence research",
        limit=5,
        source_type=["report"],
    )
    assert all(r["source_type"] == "report" for r in reports_only)

    nlp_results = await ops.search_similar_articles(
        query="language models",
        limit=5,
        category=["NLP"],
    )
    assert all(r["category"] == "NLP" for r in nlp_results)

    high_importance = await ops.search_similar_articles(
        query="AI models and techniques",
        limit=5,
        min_importance_score=0.95,
    )
    assert all(r["importance_score"] >= 0.95 for r in high_importance)

    ref_vector_id = vector_ids[0]
    similar_articles = await ops.find_similar_articles(
        vector_id=ref_vector_id,
        limit=3,
        score_threshold=0.5,
    )
    assert similar_articles
    assert all(a["vector_id"] != ref_vector_id for a in similar_articles)

    no_results = await ops.search_similar_articles(
        query="quantum computing blockchain cryptocurrency",
        limit=5,
        score_threshold=0.95,
    )
    assert isinstance(no_results, list)
