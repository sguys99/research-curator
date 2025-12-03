"""Comprehensive test suite for Day 5: Vector Database & Semantic Search.

This module combines all checkpoint tests (1-4) into a single test suite:
- Checkpoint 1: Qdrant Client & Collection Setup
- Checkpoint 2: Embedding Generation Pipeline
- Checkpoint 3: Vector CRUD Operations
- Checkpoint 4: Semantic Search
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.processors.embedder import TextEmbedder, get_embedder
from app.vector_db import (
    CollectionSchema,
    VectorOperations,
    get_qdrant_client,
    get_vector_operations,
    initialize_vector_db,
    verify_collection_schema,
)

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ==============================================================================
# Checkpoint 1: Qdrant Client & Collection Setup
# ==============================================================================


def test_checkpoint1_client_and_collection():
    """Test Qdrant client initialization and collection setup."""
    print("\n" + "=" * 70)
    print("Checkpoint 1: Qdrant Client & Collection Setup")
    print("=" * 70 + "\n")

    # Test 1: Client initialization and health check
    print("Test 1.1: Client Initialization & Health Check")
    print("-" * 70)
    client = get_qdrant_client()
    health = client.health_check()

    print(f"Status: {health['status']}")
    print(f"Connected: {health['connected']}")
    print(f"Host: {health['host']}:{health['port']}")
    print(f"Collections: {health.get('collections', [])}")

    assert health["status"] == "healthy", "Qdrant health check failed"
    print("✅ Test 1.1 passed\n")

    # Test 2: Collection schema information
    print("Test 1.2: Collection Schema Information")
    print("-" * 70)
    schema_info = CollectionSchema.get_schema_info()
    print(f"Collection Name: {schema_info['collection_name']}")
    print(f"Vector Size: {schema_info['vector_size']}")
    print(f"Distance Metric: {schema_info['distance_metric']}")
    print(f"Payload Fields: {len(schema_info['payload_schema'])} fields")
    print(f"Indexes: {len(schema_info['payload_indexes'])} indexes")
    print("✅ Test 1.2 passed\n")

    # Test 3: Full initialization
    print("Test 1.3: Full Vector DB Initialization")
    print("-" * 70)
    success = initialize_vector_db(recreate=True)
    assert success, "Vector DB initialization failed"
    print("✅ Test 1.3 passed\n")

    # Test 4: Verify collection
    print("Test 1.4: Collection Verification")
    print("-" * 70)
    verification = verify_collection_schema(client)
    print(f"Collection Exists: {verification['exists']}")
    print(f"Schema Valid: {verification['schema_valid']}")

    if verification["info"]:
        info = verification["info"]
        print(f"Vector Size: {info['vector_size']}")
        print(f"Points Count: {info['points_count']}")
        print(f"Status: {info['status']}")

    assert verification["exists"], "Collection doesn't exist"
    assert verification["schema_valid"], "Schema validation failed"
    assert not verification["errors"], f"Errors: {verification['errors']}"
    print("✅ Test 1.4 passed\n")

    print("🎉 Checkpoint 1: ALL TESTS PASSED!\n")
    return True


# ==============================================================================
# Checkpoint 2: Embedding Generation Pipeline
# ==============================================================================


async def test_checkpoint2_embedding_pipeline():
    """Test embedding generation pipeline."""
    print("\n" + "=" * 70)
    print("Checkpoint 2: Embedding Generation Pipeline")
    print("=" * 70 + "\n")

    # Test 1: Embedder initialization
    print("Test 2.1: Embedder Initialization")
    print("-" * 70)
    embedder = TextEmbedder(use_cache=True)
    print(f"Model: {embedder.model}")
    print(f"Max tokens: {embedder.MAX_TOKENS}")
    print(f"Cache enabled: {embedder.use_cache}")
    print(f"Embedding dimension: {embedder.get_embedding_dimension()}")
    print("✅ Test 2.1 passed\n")

    # Test 2: Token counting and truncation
    print("Test 2.2: Token Counting & Truncation")
    print("-" * 70)
    short_text = "Attention Is All You Need"
    long_text = "AI research " * 10000

    short_tokens = embedder.count_tokens(short_text)
    long_tokens = embedder.count_tokens(long_text)

    print(f"Short text tokens: {short_tokens}")
    print(f"Long text tokens: {long_tokens}")

    truncated = embedder.truncate_text(long_text, max_tokens=1000)
    truncated_tokens = embedder.count_tokens(truncated)
    print(f"Truncated tokens: {truncated_tokens}")

    assert short_tokens < 100, "Short text token count error"
    assert long_tokens > 10000, "Long text token count error"
    assert truncated_tokens <= 1000, "Truncation failed"
    print("✅ Test 2.2 passed\n")

    # Test 3: Single embedding generation
    print("Test 2.3: Single Embedding Generation")
    print("-" * 70)
    test_text = "Transformer architecture for NLP"
    embedding = await embedder.embed(test_text)

    print(f"Text: {test_text}")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")

    assert len(embedding) == 1536, "Embedding dimension mismatch"
    assert all(isinstance(x, float) for x in embedding), "Embedding values not floats"
    print("✅ Test 2.3 passed\n")

    # Test 4: Batch embedding generation
    print("Test 2.4: Batch Embedding Generation")
    print("-" * 70)
    texts = [
        "Attention Is All You Need",
        "BERT: Pre-training of Deep Bidirectional Transformers",
        "GPT-4 Technical Report",
    ]

    embeddings = await embedder.batch_embed(texts, batch_size=2)

    print(f"Number of texts: {len(texts)}")
    print(f"Number of embeddings: {len(embeddings)}")

    assert len(embeddings) == len(texts), "Batch embedding count mismatch"
    assert all(len(e) == 1536 for e in embeddings), "Embedding dimension mismatch"
    print("✅ Test 2.4 passed\n")

    # Test 5: Article embedding
    print("Test 2.5: Article Embedding")
    print("-" * 70)
    article_embedding = await embedder.embed_article(
        title="Attention Is All You Need",
        content="The Transformer architecture...",
        summary="Transformer 아키텍처를 제안하는 논문입니다.",
    )

    print(f"Article embedding dimension: {len(article_embedding)}")
    assert len(article_embedding) == 1536, "Article embedding dimension mismatch"
    print("✅ Test 2.5 passed\n")

    # Test 6: Cache functionality
    print("Test 2.6: Cache Functionality")
    print("-" * 70)
    cache_test_text = "Test caching mechanism"

    emb1 = await embedder.embed(cache_test_text)
    stats1 = embedder.get_cache_stats()
    print(f"After first embedding - Cache size: {stats1['size']}")

    emb2 = await embedder.embed(cache_test_text)
    print(f"Embeddings identical: {emb1 == emb2}")

    embedder.clear_cache()
    stats3 = embedder.get_cache_stats()
    print(f"After clear - Cache size: {stats3['size']}")

    assert emb1 == emb2, "Cache not working"
    assert stats3["size"] == 0, "Cache clear failed"
    print("✅ Test 2.6 passed\n")

    # Test 7: Global embedder instance
    print("Test 2.7: Global Embedder Singleton")
    print("-" * 70)
    embedder1 = get_embedder()
    embedder2 = get_embedder()
    print(f"Same instance: {embedder1 is embedder2}")

    assert embedder1 is embedder2, "Global embedder not singleton"
    print("✅ Test 2.7 passed\n")

    print("🎉 Checkpoint 2: ALL TESTS PASSED!\n")
    return True


# ==============================================================================
# Checkpoint 3: Vector CRUD Operations
# ==============================================================================


async def test_checkpoint3_vector_crud():
    """Test vector CRUD operations."""
    print("\n" + "=" * 70)
    print("Checkpoint 3: Vector CRUD Operations")
    print("=" * 70 + "\n")

    # Initialize vector DB
    print("Initializing vector database...")
    init_success = initialize_vector_db(recreate=True)
    assert init_success, "Failed to initialize vector database"
    print("✅ Vector database initialized\n")

    # Test 1: VectorOperations initialization
    print("Test 3.1: VectorOperations Initialization")
    print("-" * 70)
    ops = VectorOperations()
    print(f"Collection: {ops.collection_name}")
    print(f"Qdrant client: {ops.qdrant_client}")
    print(f"Embedder: {ops.embedder}")

    initial_count = ops.count_articles()
    print(f"Initial article count: {initial_count}")
    assert initial_count == 0, "Collection should be empty"
    print("✅ Test 3.1 passed\n")

    # Test 2: Insert single article
    print("Test 3.2: Insert Single Article")
    print("-" * 70)
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
    print(f"Inserted article with vector_id: {vector_id1}")

    count_after_insert = ops.count_articles()
    print(f"Article count after insert: {count_after_insert}")
    assert count_after_insert == 1, "Should have 1 article"
    print("✅ Test 3.2 passed\n")

    # Test 3: Get article
    print("Test 3.3: Get Article")
    print("-" * 70)
    retrieved = ops.get_article(vector_id1)
    print(f"Retrieved title: {retrieved['title']}")
    print(f"Retrieved article_id: {retrieved['article_id']}")

    assert retrieved is not None, "Article should be found"
    assert retrieved["title"] == article1["title"], "Title mismatch"
    print("✅ Test 3.3 passed\n")

    # Test 4: Batch insert articles
    print("Test 3.4: Batch Insert Articles")
    print("-" * 70)
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
    print(f"Batch inserted {len(vector_ids)} articles")

    count_after_batch = ops.count_articles()
    assert count_after_batch == 3, "Should have 3 articles total"
    print("✅ Test 3.4 passed\n")

    # Test 5: Get articles batch
    print("Test 3.5: Get Articles Batch")
    print("-" * 70)
    all_vector_ids = [vector_id1] + vector_ids
    retrieved_batch = ops.get_articles_batch(all_vector_ids)

    print(f"Retrieved {len(retrieved_batch)} articles")
    assert len(retrieved_batch) == 3, "Should retrieve 3 articles"
    print("✅ Test 3.5 passed\n")

    # Test 6: Update article
    print("Test 3.6: Update Article")
    print("-" * 70)
    update_success = await ops.update_article(
        vector_id=vector_id1,
        importance_score=0.99,
        category="NLP/Transformers",
    )

    updated = ops.get_article(vector_id1)
    print(f"Updated importance_score: {updated['importance_score']}")
    print(f"Updated category: {updated['category']}")

    assert update_success, "Update should succeed"
    assert updated["importance_score"] == 0.99, "Score should be updated"
    print("✅ Test 3.6 passed\n")

    # Test 7: Delete single article
    print("Test 3.7: Delete Single Article")
    print("-" * 70)
    delete_success = ops.delete_article(vector_ids[0])

    count_after_delete = ops.count_articles()
    print(f"Article count after delete: {count_after_delete}")

    assert delete_success, "Delete should succeed"
    assert count_after_delete == 2, "Should have 2 articles remaining"
    print("✅ Test 3.7 passed\n")

    # Test 8: Delete articles batch
    print("Test 3.8: Delete Articles Batch")
    print("-" * 70)
    remaining_ids = [vector_id1, vector_ids[1]]
    batch_delete_success = ops.delete_articles_batch(remaining_ids)

    final_count = ops.count_articles()
    print(f"Final article count: {final_count}")

    assert batch_delete_success, "Batch delete should succeed"
    assert final_count == 0, "Collection should be empty"
    print("✅ Test 3.8 passed\n")

    # Test 9: Global operations instance
    print("Test 3.9: Global VectorOperations Singleton")
    print("-" * 70)
    ops1 = get_vector_operations()
    ops2 = get_vector_operations()
    print(f"Same instance: {ops1 is ops2}")

    assert ops1 is ops2, "Global operations should be singleton"
    print("✅ Test 3.9 passed\n")

    print("🎉 Checkpoint 3: ALL TESTS PASSED!\n")
    return True


# ==============================================================================
# Checkpoint 4: Semantic Search
# ==============================================================================


async def test_checkpoint4_semantic_search():
    """Test semantic search functionality."""
    print("\n" + "=" * 70)
    print("Checkpoint 4: Semantic Search")
    print("=" * 70 + "\n")

    # Initialize vector DB
    print("Initializing vector database...")
    init_success = initialize_vector_db(recreate=True)
    assert init_success, "Failed to initialize vector database"
    print("✅ Vector database initialized\n")

    ops = VectorOperations()

    # Prepare test articles
    test_articles = [
        {
            "article_id": "uuid-1",
            "title": "Attention Is All You Need",
            "content": "The dominant sequence transduction models are based on "
            "complex recurrent or convolutional neural networks. "
            "We propose the Transformer, based solely on attention mechanisms.",
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

    # Insert test articles
    print("Inserting test articles...")
    vector_ids = await ops.insert_articles_batch(test_articles, batch_size=2)
    print(f"Inserted {len(vector_ids)} articles\n")

    # Test 1: Basic semantic search
    print("Test 4.1: Basic Semantic Search")
    print("-" * 70)
    query1 = "transformer architecture and attention mechanism"
    results1 = await ops.search_similar_articles(query=query1, limit=3, score_threshold=0.5)

    print(f"Query: '{query1}'")
    print(f"Results found: {len(results1)}")

    assert len(results1) > 0, "Should find results"
    assert results1[0]["score"] > 0.5, "Top result should have reasonable score"
    print("✅ Test 4.1 passed\n")

    # Test 2: Search with score threshold
    print("Test 4.2: Search with Score Threshold")
    print("-" * 70)
    query2 = "natural language processing models"
    results2_high = await ops.search_similar_articles(query=query2, limit=10, score_threshold=0.85)
    results2_low = await ops.search_similar_articles(query=query2, limit=10, score_threshold=0.70)

    print(f"Query: '{query2}'")
    print(f"Results (threshold=0.85): {len(results2_high)}")
    print(f"Results (threshold=0.70): {len(results2_low)}")

    assert len(results2_low) >= len(results2_high), "Lower threshold should return more"
    print("✅ Test 4.2 passed\n")

    # Test 3: Filter by source type
    print("Test 4.3: Filter by Source Type")
    print("-" * 70)
    query3 = "artificial intelligence research"
    papers_only = await ops.search_similar_articles(query=query3, limit=5, source_type=["paper"])
    reports_only = await ops.search_similar_articles(query=query3, limit=5, source_type=["report"])

    print(f"Papers only: {len(papers_only)} results")
    print(f"Reports only: {len(reports_only)} results")

    assert all(r["source_type"] == "paper" for r in papers_only), "Should only return papers"
    assert all(r["source_type"] == "report" for r in reports_only), "Should only return reports"
    print("✅ Test 4.3 passed\n")

    # Test 4: Filter by category
    print("Test 4.4: Filter by Category")
    print("-" * 70)
    query4 = "language models"
    nlp_results = await ops.search_similar_articles(query=query4, limit=5, category=["NLP"])

    print(f"NLP category only: {len(nlp_results)} results")

    assert all(r["category"] == "NLP" for r in nlp_results), "Should only return NLP"
    print("✅ Test 4.4 passed\n")

    # Test 5: Filter by importance score
    print("Test 4.5: Filter by Importance Score")
    print("-" * 70)
    query5 = "AI models and techniques"
    high_importance = await ops.search_similar_articles(query=query5, limit=5, min_importance_score=0.95)

    print(f"High importance (≥0.95): {len(high_importance)} results")

    assert all(
        r["importance_score"] >= 0.95 for r in high_importance
    ), "Should only return high importance"
    print("✅ Test 4.5 passed\n")

    # Test 6: Find similar articles by vector_id
    print("Test 4.6: Find Similar Articles (by vector_id)")
    print("-" * 70)
    ref_vector_id = vector_ids[0]
    similar_articles = await ops.find_similar_articles(
        vector_id=ref_vector_id,
        limit=3,
        score_threshold=0.5,
    )

    print(f"Reference vector_id: {ref_vector_id}")
    print(f"Similar articles found: {len(similar_articles)}")

    assert len(similar_articles) > 0, "Should find similar articles"
    assert all(a["vector_id"] != ref_vector_id for a in similar_articles), "Should not include reference"
    print("✅ Test 4.6 passed\n")

    # Test 7: Edge case - No results
    print("Test 4.7: Edge Case - No Results")
    print("-" * 70)
    no_results = await ops.search_similar_articles(
        query="quantum computing blockchain cryptocurrency",
        limit=5,
        score_threshold=0.95,
    )

    print(f"Results: {len(no_results)}")

    assert isinstance(no_results, list), "Should return empty list, not error"
    print("✅ Test 4.7 passed\n")

    print("🎉 Checkpoint 4: ALL TESTS PASSED!\n")
    return True


# ==============================================================================
# Main Test Runner
# ==============================================================================


async def run_all_tests():
    """Run all checkpoint tests sequentially."""
    print("\n" + "=" * 70)
    print("DAY 5: VECTOR DATABASE & SEMANTIC SEARCH - FULL TEST SUITE")
    print("=" * 70)

    try:
        # Checkpoint 1: Qdrant Client & Collection
        test_checkpoint1_client_and_collection()

        # Checkpoint 2: Embedding Pipeline
        await test_checkpoint2_embedding_pipeline()

        # Checkpoint 3: Vector CRUD Operations
        await test_checkpoint3_vector_crud()

        # Checkpoint 4: Semantic Search
        await test_checkpoint4_semantic_search()

        # Final summary
        print("\n" + "=" * 70)
        print("🎉 ALL CHECKPOINTS PASSED! 🎉")
        print("=" * 70)
        print("\n✅ Checkpoint 1: Qdrant Client & Collection Setup")
        print("✅ Checkpoint 2: Embedding Generation Pipeline")
        print("✅ Checkpoint 3: Vector CRUD Operations")
        print("✅ Checkpoint 4: Semantic Search")
        print("\n🚀 Day 5 Complete! Vector DB system ready for production.\n")

        return True

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
