"""Quick test script for Day 5 Checkpoint 4: Semantic Search."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app.vector_db import VectorOperations, initialize_vector_db

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def main():
    """Run checkpoint 4 tests."""
    print("\n" + "=" * 60)
    print("Day 5 Checkpoint 4: Semantic Search")
    print("=" * 60 + "\n")

    # Initialize vector DB
    print("Initializing vector database...")
    init_success = initialize_vector_db(recreate=True)
    if not init_success:
        print("❌ Failed to initialize vector database")
        return False
    print("✅ Vector database initialized\n")

    ops = VectorOperations()

    # Prepare test articles
    test_articles = [
        {
            "article_id": "uuid-1",
            "title": "Attention Is All You Need",
            "content": """
            The dominant sequence transduction models are based on complex recurrent
            or convolutional neural networks. We propose a new simple network architecture,
            the Transformer, based solely on attention mechanisms.
            """,
            "summary": "Transformer 아키텍처를 소개하는 혁신적인 논문입니다.",
            "source_type": "paper",
            "category": "NLP",
            "importance_score": 0.95,
        },
        {
            "article_id": "uuid-2",
            "title": "BERT: Pre-training of Deep Bidirectional Transformers",
            "content": """
            We introduce BERT, a new language representation model which obtains
            state-of-the-art results on eleven natural language processing tasks.
            """,
            "summary": "BERT 모델을 소개합니다.",
            "source_type": "paper",
            "category": "NLP",
            "importance_score": 0.92,
        },
        {
            "article_id": "uuid-3",
            "title": "GPT-4 Technical Report",
            "content": """
            GPT-4 is a large-scale, multimodal model which can accept image and text inputs
            and produce text outputs.
            """,
            "summary": "GPT-4의 기술적 세부사항을 다룹니다.",
            "source_type": "report",
            "category": "AI",
            "importance_score": 0.98,
        },
        {
            "article_id": "uuid-4",
            "title": "Efficient Transformers: A Survey",
            "content": """
            This survey provides a comprehensive overview of efficient Transformer models,
            discussing various approaches to reduce computational complexity.
            """,
            "summary": "효율적인 Transformer 모델들을 조사합니다.",
            "source_type": "paper",
            "category": "NLP",
            "importance_score": 0.88,
        },
        {
            "article_id": "uuid-5",
            "title": "OpenAI Announces New AI Safety Research",
            "content": """
            OpenAI has announced a new initiative focusing on AI alignment and safety research
            to ensure beneficial AI development.
            """,
            "summary": "OpenAI의 AI 안전성 연구 발표입니다.",
            "source_type": "news",
            "category": "AI Safety",
            "importance_score": 0.85,
        },
        {
            "article_id": "uuid-6",
            "title": "Scaling Laws for Neural Language Models",
            "content": """
            We study empirical scaling laws for language model performance,
            examining the relationships between model size, dataset size, and compute.
            """,
            "summary": "언어 모델의 스케일링 법칙을 연구합니다.",
            "source_type": "paper",
            "category": "AI",
            "importance_score": 0.90,
        },
    ]

    # Insert test articles
    print("Inserting test articles...")
    vector_ids = await ops.insert_articles_batch(test_articles, batch_size=3)
    print(f"Inserted {len(vector_ids)} articles\n")

    # Test 1: Basic semantic search
    print("Test 1: Basic Semantic Search")
    print("-" * 60)
    query1 = "transformer architecture and attention mechanism"
    results1 = await ops.search_similar_articles(query=query1, limit=3, score_threshold=0.5)

    print(f"Query: '{query1}'")
    print(f"Results found: {len(results1)}\n")
    for i, result in enumerate(results1, 1):
        print(f"[{i}] Score: {result['score']:.4f}")
        print(f"    Title: {result['title']}")
        print(f"    Category: {result['category']}")
        print()

    assert len(results1) > 0, "Should find results"
    assert results1[0]["score"] > 0.5, "Top result should have reasonable score"
    print("✅ Test 1 passed\n")

    # Test 2: Search with score threshold
    print("Test 2: Search with Score Threshold")
    print("-" * 60)
    query2 = "natural language processing models"
    results2_high = await ops.search_similar_articles(
        query=query2,
        limit=10,
        score_threshold=0.85,
    )
    results2_low = await ops.search_similar_articles(
        query=query2,
        limit=10,
        score_threshold=0.70,
    )

    print(f"Query: '{query2}'")
    print(f"Results (threshold=0.85): {len(results2_high)}")
    print(f"Results (threshold=0.70): {len(results2_low)}")
    print()

    assert len(results2_low) >= len(results2_high), "Lower threshold should return more results"
    assert all(r["score"] >= 0.85 for r in results2_high), "All results should meet threshold"
    print("✅ Test 2 passed\n")

    # Test 3: Filter by source type
    print("Test 3: Filter by Source Type")
    print("-" * 60)
    query3 = "artificial intelligence research"
    papers_only = await ops.search_similar_articles(
        query=query3,
        limit=5,
        source_type=["paper"],
    )
    news_only = await ops.search_similar_articles(
        query=query3,
        limit=5,
        source_type=["news"],
    )

    print(f"Query: '{query3}'")
    print(f"Papers only: {len(papers_only)} results")
    for r in papers_only:
        print(f"  - {r['title'][:40]}... (type: {r['source_type']})")

    print(f"\nNews only: {len(news_only)} results")
    for r in news_only:
        print(f"  - {r['title'][:40]}... (type: {r['source_type']})")
    print()

    assert all(r["source_type"] == "paper" for r in papers_only), "Should only return papers"
    assert all(r["source_type"] == "news" for r in news_only), "Should only return news"
    print("✅ Test 3 passed\n")

    # Test 4: Filter by category
    print("Test 4: Filter by Category")
    print("-" * 60)
    query4 = "language models"
    nlp_results = await ops.search_similar_articles(
        query=query4,
        limit=5,
        category=["NLP"],
    )

    print(f"Query: '{query4}'")
    print(f"NLP category only: {len(nlp_results)} results")
    for r in nlp_results:
        print(f"  - {r['title'][:40]}... (category: {r['category']})")
    print()

    assert all(r["category"] == "NLP" for r in nlp_results), "Should only return NLP category"
    print("✅ Test 4 passed\n")

    # Test 5: Filter by importance score
    print("Test 5: Filter by Importance Score")
    print("-" * 60)
    query5 = "AI models and techniques"
    high_importance = await ops.search_similar_articles(
        query=query5,
        limit=5,
        min_importance_score=0.9,
    )

    print(f"Query: '{query5}'")
    print(f"High importance (≥0.9): {len(high_importance)} results")
    for r in high_importance:
        print(f"  - {r['title'][:40]}... (score: {r['importance_score']})")
    print()

    assert all(
        r["importance_score"] >= 0.9 for r in high_importance
    ), "Should only return high importance articles"
    print("✅ Test 5 passed\n")

    # Test 6: Combined filters
    print("Test 6: Combined Filters")
    print("-" * 60)
    query6 = "transformer models"
    combined_results = await ops.search_similar_articles(
        query=query6,
        limit=5,
        score_threshold=0.75,
        source_type=["paper"],
        category=["NLP"],
        min_importance_score=0.85,
    )

    print(f"Query: '{query6}'")
    print("Filters: papers + NLP + importance≥0.85 + score≥0.75")
    print(f"Results: {len(combined_results)}")
    for r in combined_results:
        print(f"  - {r['title'][:40]}...")
        print(f"    Type: {r['source_type']}, Category: {r['category']}")
        print(f"    Importance: {r['importance_score']}, Similarity: {r['score']:.4f}")
    print()

    for r in combined_results:
        assert r["source_type"] == "paper", "Should be paper"
        assert r["category"] == "NLP", "Should be NLP"
        assert r["importance_score"] >= 0.85, "Should meet importance threshold"
        assert r["score"] >= 0.75, "Should meet similarity threshold"
    print("✅ Test 6 passed\n")

    # Test 7: Find similar articles by vector_id
    print("Test 7: Find Similar Articles (by vector_id)")
    print("-" * 60)
    ref_vector_id = vector_ids[0]  # "Attention Is All You Need"
    similar_articles = await ops.find_similar_articles(
        vector_id=ref_vector_id,
        limit=3,
        score_threshold=0.5,
    )

    print(f"Reference article vector_id: {ref_vector_id}")
    print(f"Similar articles found: {len(similar_articles)}\n")
    for i, article in enumerate(similar_articles, 1):
        print(f"[{i}] Score: {article['score']:.4f}")
        print(f"    Title: {article['title']}")
        print()

    assert len(similar_articles) > 0, "Should find similar articles"
    assert all(
        a["vector_id"] != ref_vector_id for a in similar_articles
    ), "Should not include reference article"
    print("✅ Test 7 passed\n")

    # Test 8: Find similar articles with filters
    print("Test 8: Find Similar Articles with Filters")
    print("-" * 60)
    similar_papers = await ops.find_similar_articles(
        vector_id=vector_ids[0],
        limit=5,
        source_type=["paper"],
        category=["NLP"],
    )

    print("Finding similar papers in NLP category")
    print(f"Results: {len(similar_papers)}")
    for r in similar_papers:
        print(f"  - {r['title'][:40]}... ({r['source_type']}, {r['category']})")
    print()

    assert all(r["source_type"] == "paper" for r in similar_papers), "Should only return papers"
    print("✅ Test 8 passed\n")

    # Test 9: Empty search results
    print("Test 9: Edge Case - No Results")
    print("-" * 60)
    no_results = await ops.search_similar_articles(
        query="quantum computing blockchain cryptocurrency",
        limit=5,
        score_threshold=0.95,  # Very high threshold
    )

    print("Query with very high threshold (0.95)")
    print(f"Results: {len(no_results)}")

    assert isinstance(no_results, list), "Should return empty list, not error"
    print("✅ Test 9 passed\n")

    # Final summary
    print("=" * 60)
    print("🎉 ALL TESTS PASSED! 🎉")
    print("=" * 60)
    print("\n✅ Basic semantic search working")
    print("✅ Score threshold filtering working")
    print("✅ Source type filtering working")
    print("✅ Category filtering working")
    print("✅ Importance score filtering working")
    print("✅ Combined filters working")
    print("✅ Find similar articles (by vector_id) working")
    print("✅ Find similar with filters working")
    print("✅ Edge case handling working")
    print("\n🚀 Ready for Checkpoint 5: Integration & Optimization\n")

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
