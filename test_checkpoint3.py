"""Quick test script for Day 5 Checkpoint 3: Vector CRUD Operations."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app.vector_db import VectorOperations, get_vector_operations, initialize_vector_db

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def main():
    """Run checkpoint 3 tests."""
    print("\n" + "=" * 60)
    print("Day 5 Checkpoint 3: Vector CRUD Operations")
    print("=" * 60 + "\n")

    # Initialize vector DB
    print("Initializing vector database...")
    init_success = initialize_vector_db(recreate=True)
    if not init_success:
        print("❌ Failed to initialize vector database")
        return False
    print("✅ Vector database initialized\n")

    # Test 1: VectorOperations initialization
    print("Test 1: VectorOperations Initialization")
    print("-" * 60)
    ops = VectorOperations()
    print(f"Collection: {ops.collection_name}")
    print(f"Qdrant client: {ops.qdrant_client}")
    print(f"Embedder: {ops.embedder}")

    # Check initial count
    initial_count = ops.count_articles()
    print(f"Initial article count: {initial_count}")
    assert initial_count == 0, "Collection should be empty"
    print("✅ Test 1 passed\n")

    # Test 2: Insert single article
    print("Test 2: Insert Single Article")
    print("-" * 60)
    article1 = {
        "article_id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Attention Is All You Need",
        "content": """
        The dominant sequence transduction models are based on complex recurrent
        or convolutional neural networks that include an encoder and a decoder.
        We propose a new simple network architecture, the Transformer, based solely
        on attention mechanisms, dispensing with recurrence and convolutions entirely.
        """,
        "summary": "Transformer 아키텍처를 제안하는 혁신적인 논문입니다.",
        "source_type": "paper",
        "category": "NLP",
        "importance_score": 0.95,
        "metadata": {"authors": ["Vaswani et al."], "year": 2017},
    }

    vector_id1 = await ops.insert_article(**article1)
    print(f"Inserted article with vector_id: {vector_id1}")

    # Verify insertion
    count_after_insert = ops.count_articles()
    print(f"Article count after insert: {count_after_insert}")
    assert count_after_insert == 1, "Should have 1 article"
    print("✅ Test 2 passed\n")

    # Test 3: Get article
    print("Test 3: Get Article")
    print("-" * 60)
    retrieved = ops.get_article(vector_id1)
    print(f"Retrieved article title: {retrieved['title']}")
    print(f"Retrieved article_id: {retrieved['article_id']}")
    print(f"Retrieved importance_score: {retrieved['importance_score']}")

    assert retrieved is not None, "Article should be found"
    assert retrieved["title"] == article1["title"], "Title mismatch"
    assert retrieved["article_id"] == article1["article_id"], "Article ID mismatch"
    print("✅ Test 3 passed\n")

    # Test 4: Batch insert articles
    print("Test 4: Batch Insert Articles")
    print("-" * 60)
    articles_batch = [
        {
            "article_id": "223e4567-e89b-12d3-a456-426614174001",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "content": "BERT is designed to pre-train deep bidirectional representations...",
            "summary": "BERT 모델을 소개하는 논문입니다.",
            "source_type": "paper",
            "category": "NLP",
            "importance_score": 0.92,
        },
        {
            "article_id": "323e4567-e89b-12d3-a456-426614174002",
            "title": "GPT-4 Technical Report",
            "content": "GPT-4 is a large-scale, multimodal model...",
            "summary": "GPT-4의 기술 리포트입니다.",
            "source_type": "report",
            "category": "AI",
            "importance_score": 0.98,
        },
        {
            "article_id": "423e4567-e89b-12d3-a456-426614174003",
            "title": "AI Safety Research at OpenAI",
            "content": "OpenAI's approach to AI safety...",
            "summary": "OpenAI의 AI 안전성 연구를 다룹니다.",
            "source_type": "news",
            "category": "AI Safety",
            "importance_score": 0.85,
        },
    ]

    vector_ids = await ops.insert_articles_batch(articles_batch, batch_size=2)
    print(f"Batch inserted {len(vector_ids)} articles")
    print(f"Vector IDs: {vector_ids}")

    count_after_batch = ops.count_articles()
    print(f"Article count after batch insert: {count_after_batch}")
    assert count_after_batch == 4, "Should have 4 articles total"
    assert len(vector_ids) == 3, "Should return 3 vector IDs"
    print("✅ Test 4 passed\n")

    # Test 5: Get articles batch
    print("Test 5: Get Articles Batch")
    print("-" * 60)
    all_vector_ids = [vector_id1] + vector_ids
    retrieved_batch = ops.get_articles_batch(all_vector_ids)

    print(f"Retrieved {len(retrieved_batch)} articles")
    for i, article in enumerate(retrieved_batch, 1):
        print(f"[{i}] {article['title'][:40]}... (score: {article['importance_score']})")

    assert len(retrieved_batch) == 4, "Should retrieve 4 articles"
    print("✅ Test 5 passed\n")

    # Test 6: Update article
    print("Test 6: Update Article")
    print("-" * 60)
    update_success = await ops.update_article(
        vector_id=vector_id1,
        importance_score=0.99,
        category="NLP/Transformers",
    )

    print(f"Update success: {update_success}")

    # Verify update
    updated = ops.get_article(vector_id1)
    print(f"Updated importance_score: {updated['importance_score']}")
    print(f"Updated category: {updated['category']}")

    assert update_success, "Update should succeed"
    assert updated["importance_score"] == 0.99, "Importance score should be updated"
    assert updated["category"] == "NLP/Transformers", "Category should be updated"
    print("✅ Test 6 passed\n")

    # Test 7: Delete single article
    print("Test 7: Delete Single Article")
    print("-" * 60)
    delete_success = ops.delete_article(vector_ids[0])
    print(f"Delete success: {delete_success}")

    count_after_delete = ops.count_articles()
    print(f"Article count after delete: {count_after_delete}")

    assert delete_success, "Delete should succeed"
    assert count_after_delete == 3, "Should have 3 articles remaining"

    # Verify deletion
    deleted_article = ops.get_article(vector_ids[0])
    assert deleted_article is None, "Deleted article should not be found"
    print("✅ Test 7 passed\n")

    # Test 8: Delete articles batch
    print("Test 8: Delete Articles Batch")
    print("-" * 60)
    remaining_ids = [vector_id1, vector_ids[1], vector_ids[2]]
    batch_delete_success = ops.delete_articles_batch(remaining_ids)
    print(f"Batch delete success: {batch_delete_success}")

    final_count = ops.count_articles()
    print(f"Final article count: {final_count}")

    assert batch_delete_success, "Batch delete should succeed"
    assert final_count == 0, "Collection should be empty"
    print("✅ Test 8 passed\n")

    # Test 9: Global operations instance
    print("Test 9: Global VectorOperations Singleton")
    print("-" * 60)
    ops1 = get_vector_operations()
    ops2 = get_vector_operations()

    print(f"Operations 1: {ops1.collection_name}")
    print(f"Operations 2: {ops2.collection_name}")
    print(f"Same instance: {ops1 is ops2}")

    assert ops1 is ops2, "Global operations should be singleton"
    print("✅ Test 9 passed\n")

    # Final summary
    print("=" * 60)
    print("🎉 ALL TESTS PASSED! 🎉")
    print("=" * 60)
    print("\n✅ VectorOperations initialization working")
    print("✅ Single article insertion working")
    print("✅ Article retrieval working")
    print("✅ Batch article insertion working")
    print("✅ Batch article retrieval working")
    print("✅ Article update working")
    print("✅ Single article deletion working")
    print("✅ Batch article deletion working")
    print("✅ Global singleton working")
    print("\n🚀 Ready for Checkpoint 4: Semantic Search\n")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)
