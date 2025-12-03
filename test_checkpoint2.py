"""Quick test script for Day 5 Checkpoint 2: Embedding Pipeline."""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from app.processors.embedder import TextEmbedder, get_embedder

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def main():
    """Run checkpoint 2 tests."""
    print("\n" + "=" * 60)
    print("Day 5 Checkpoint 2: Embedding Generation Pipeline")
    print("=" * 60 + "\n")

    # Test 1: Embedder initialization
    print("Test 1: Embedder Initialization")
    print("-" * 60)
    embedder = TextEmbedder(use_cache=True)
    print(f"Model: {embedder.model}")
    print(f"Max tokens: {embedder.MAX_TOKENS}")
    print(f"Cache enabled: {embedder.use_cache}")
    print(f"Embedding dimension: {embedder.get_embedding_dimension()}")
    print("✅ Test 1 passed\n")

    # Test 2: Token counting and truncation
    print("Test 2: Token Counting & Truncation")
    print("-" * 60)
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
    print("✅ Test 2 passed\n")

    # Test 3: Single embedding generation
    print("Test 3: Single Embedding Generation")
    print("-" * 60)
    test_text = "Transformer architecture for NLP"
    embedding = await embedder.embed(test_text)

    print(f"Text: {test_text}")
    print(f"Embedding dimension: {len(embedding)}")
    print(f"First 5 values: {embedding[:5]}")
    print(f"Vector norm: {sum(x**2 for x in embedding) ** 0.5:.4f}")

    assert len(embedding) == 1536, "Embedding dimension mismatch"
    assert all(isinstance(x, float) for x in embedding), "Embedding values not floats"
    print("✅ Test 3 passed\n")

    # Test 4: Batch embedding generation
    print("Test 4: Batch Embedding Generation")
    print("-" * 60)
    texts = [
        "Attention Is All You Need",
        "BERT: Pre-training of Deep Bidirectional Transformers",
        "GPT-4 Technical Report",
        "Large Language Models are Few-Shot Learners",
        "Learning Transferable Visual Models From Natural Language Supervision",
    ]

    embeddings = await embedder.batch_embed(texts, batch_size=3)

    print(f"Number of texts: {len(texts)}")
    print(f"Number of embeddings: {len(embeddings)}")
    print(f"All embeddings valid: {all(len(e) == 1536 for e in embeddings)}")

    for i, (text, emb) in enumerate(zip(texts, embeddings, strict=False), 1):
        tokens = embedder.count_tokens(text)
        print(f"[{i}] {text[:40]}... ({tokens} tokens): {len(emb)} dims")

    assert len(embeddings) == len(texts), "Batch embedding count mismatch"
    assert all(len(e) == 1536 for e in embeddings), "Some embeddings have wrong dimension"
    print("✅ Test 4 passed\n")

    # Test 5: Article embedding
    print("Test 5: Article Embedding")
    print("-" * 60)
    article = {
        "title": "Attention Is All You Need",
        "content": """
        The dominant sequence transduction models are based on complex recurrent
        or convolutional neural networks that include an encoder and a decoder.
        The best performing models also connect the encoder and decoder through
        an attention mechanism. We propose a new simple network architecture,
        the Transformer, based solely on attention mechanisms, dispensing with
        recurrence and convolutions entirely.
        """,
        "summary": "Transformer 아키텍처를 제안하는 혁신적인 논문입니다.",
    }

    # Prepare article text
    article_text = embedder.prepare_article_text(
        title=article["title"],
        content=article["content"],
        summary=article["summary"],
    )

    print(f"Article title: {article['title']}")
    print(f"Prepared text length: {len(article_text)} chars")
    print(f"Prepared text tokens: {embedder.count_tokens(article_text)}")

    # Generate embedding
    article_embedding = await embedder.embed_article(
        title=article["title"],
        content=article["content"],
        summary=article["summary"],
    )

    print(f"Article embedding dimension: {len(article_embedding)}")

    assert len(article_embedding) == 1536, "Article embedding dimension mismatch"
    print("✅ Test 5 passed\n")

    # Test 6: Cache functionality
    print("Test 6: Cache Functionality")
    print("-" * 60)
    cache_test_text = "Test caching mechanism"

    # First embedding (cache miss)
    emb1 = await embedder.embed(cache_test_text)
    stats1 = embedder.get_cache_stats()
    print(f"After first embedding - Cache size: {stats1['size']}")

    # Second embedding (cache hit)
    emb2 = await embedder.embed(cache_test_text)
    stats2 = embedder.get_cache_stats()
    print(f"After second embedding - Cache size: {stats2['size']}")
    print(f"Embeddings identical: {emb1 == emb2}")

    # Clear cache
    embedder.clear_cache()
    stats3 = embedder.get_cache_stats()
    print(f"After clear - Cache size: {stats3['size']}")

    assert emb1 == emb2, "Cache not working - embeddings differ"
    assert stats3["size"] == 0, "Cache clear failed"
    print("✅ Test 6 passed\n")

    # Test 7: Batch article embedding
    print("Test 7: Batch Article Embedding")
    print("-" * 60)
    articles = [
        {
            "title": "Paper 1: Transformers",
            "content": "Content about transformers...",
            "summary": "Summary 1",
        },
        {
            "title": "Paper 2: BERT",
            "content": "Content about BERT...",
            "summary": "Summary 2",
        },
        {
            "title": "Paper 3: GPT",
            "content": "Content about GPT...",
            "summary": "Summary 3",
        },
    ]

    batch_embeddings = await embedder.embed_articles_batch(articles, batch_size=2)

    print(f"Number of articles: {len(articles)}")
    print(f"Number of embeddings: {len(batch_embeddings)}")

    for i, (article, emb) in enumerate(zip(articles, batch_embeddings, strict=False), 1):
        print(f"[{i}] {article['title']}: {len(emb)} dims")

    assert len(batch_embeddings) == len(articles), "Batch article embedding count mismatch"
    print("✅ Test 7 passed\n")

    # Test 8: Global embedder instance
    print("Test 8: Global Embedder Singleton")
    print("-" * 60)
    embedder1 = get_embedder()
    embedder2 = get_embedder()

    print(f"Embedder 1: {embedder1.model}")
    print(f"Embedder 2: {embedder2.model}")
    print(f"Same instance: {embedder1 is embedder2}")

    assert embedder1 is embedder2, "Global embedder not singleton"
    print("✅ Test 8 passed\n")

    # Final summary
    print("=" * 60)
    print("🎉 ALL TESTS PASSED! 🎉")
    print("=" * 60)
    print("\n✅ Embedder initialization working")
    print("✅ Token counting and truncation working")
    print("✅ Single embedding generation working")
    print("✅ Batch embedding generation working")
    print("✅ Article embedding working")
    print("✅ Cache functionality working")
    print("✅ Batch article embedding working")
    print("✅ Global singleton working")
    print("\n🚀 Ready for Checkpoint 3: Vector CRUD Operations\n")

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
