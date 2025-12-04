"""Scheduled tasks for data collection, processing, and email sending."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from app.collectors.arxiv import ArxivCollector
from app.collectors.news import NewsCollector
from app.core.retry import with_retry
from app.db import crud
from app.db.session import SessionLocal
from app.email.digest import send_daily_digest
from app.processors.classifier import ContentClassifier
from app.processors.embedder import TextEmbedder
from app.processors.evaluator import ImportanceEvaluator
from app.processors.summarizer import ArticleSummarizer

logger = logging.getLogger(__name__)


# Helper functions to wrap async calls
def summarize_article(title: str, content: str) -> str:
    """Synchronous wrapper for article summarization."""
    summarizer = ArticleSummarizer()
    return asyncio.run(summarizer.summarize(title=title, content=content))


def evaluate_importance(title: str, content: str) -> float:
    """Synchronous wrapper for importance evaluation."""
    evaluator = ImportanceEvaluator()
    result = asyncio.run(evaluator.evaluate(title=title, content=content))
    return result.get("importance_score", 0.5)


def classify_article_type(title: str, content: str) -> str:
    """Synchronous wrapper for article classification."""
    classifier = ContentClassifier()
    result = asyncio.run(classifier.classify(title=title, content=content))
    return result.get("category", "other")


def generate_embedding(text: str) -> list[float]:
    """Synchronous wrapper for embedding generation."""
    embedder = TextEmbedder()
    return asyncio.run(embedder.embed(text))


def collect_data_task() -> None:
    """
    Scheduled task for collecting data from various sources.

    Collects articles from:
    - arXiv (research papers)
    - News sources (TechCrunch, etc.)
    - Google Scholar (future)

    Runs daily at 01:00 KST
    """
    logger.info("=" * 60)
    logger.info("Starting data collection task...")
    logger.info(f"Timestamp: {datetime.now(UTC).isoformat()}")
    logger.info("=" * 60)

    db = SessionLocal()
    collected_count = 0
    error_count = 0

    try:
        # Get all users with preferences to determine what to collect
        users = crud.list_users(db)
        logger.info(f"Found {len(users)} users")

        if not users:
            logger.warning("No users found, skipping data collection")
            return

        # Aggregate all research fields and keywords from users
        all_fields = set()
        all_keywords = set()

        for user in users:
            pref = crud.get_user_preference(db, user.id)
            if pref:
                all_fields.update(pref.research_fields)
                all_keywords.update(pref.keywords)

        logger.info(f"Collecting for {len(all_fields)} fields and {len(all_keywords)} keywords")

        # 1. Collect from arXiv
        logger.info("\n1. Collecting from arXiv...")
        arxiv_collector = ArxivCollector()

        for field in all_fields:
            try:
                articles = with_retry(
                    lambda f=field: asyncio.run(arxiv_collector.collect(query=f, max_results=5)),
                    max_attempts=3,
                )

                for article_data in articles:
                    # Check if article already exists
                    existing = crud.get_article_by_url(db, article_data.url)
                    if existing:
                        logger.debug(f"Article already exists: {article_data.title[:50]}...")
                        continue

                    # Create article
                    crud.create_article(
                        db=db,
                        title=article_data.title,
                        content=article_data.content,
                        source_url=article_data.url,
                        source_type="paper",
                        article_metadata=article_data.metadata,
                    )
                    collected_count += 1
                    logger.info(f"✅ Collected from arXiv: {article_data.title[:60]}...")

            except Exception as e:
                logger.error(f"Error collecting from arXiv for field '{field}': {e}")
                error_count += 1

        # 2. Collect from News sources
        logger.info("\n2. Collecting from News sources...")
        news_collector = NewsCollector()

        for keyword in list(all_keywords)[:5]:  # Limit to 5 keywords to avoid rate limits
            try:
                articles = with_retry(
                    lambda k=keyword: asyncio.run(news_collector.collect(query=k, max_results=3)),
                    max_attempts=3,
                )

                for article_data in articles:
                    existing = crud.get_article_by_url(db, article_data.url)
                    if existing:
                        continue

                    crud.create_article(
                        db=db,
                        title=article_data.title,
                        content=article_data.content,
                        source_url=article_data.url,
                        source_type="news",
                        article_metadata=article_data.metadata,
                    )
                    collected_count += 1
                    logger.info(f"✅ Collected from News: {article_data.title[:60]}...")

            except Exception as e:
                logger.error(f"Error collecting news for keyword '{keyword}': {e}")
                error_count += 1

        logger.info("\n" + "=" * 60)
        logger.info("✅ Data collection completed!")
        logger.info(f"Total collected: {collected_count} articles")
        logger.info(f"Errors: {error_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Fatal error in data collection task: {e}", exc_info=True)
    finally:
        db.close()


def process_articles_task() -> None:
    """
    Scheduled task for processing collected articles.

    Processing steps:
    1. Summarize content (Korean)
    2. Evaluate importance score
    3. Classify article type
    4. Generate embeddings
    5. Store in Vector DB

    Runs daily at 01:30 KST
    """
    logger.info("=" * 60)
    logger.info("Starting article processing task...")
    logger.info(f"Timestamp: {datetime.now(UTC).isoformat()}")
    logger.info("=" * 60)

    db = SessionLocal()
    processed_count = 0
    error_count = 0

    try:
        # Get articles collected in the last 24 hours that haven't been processed
        articles = crud.list_articles(db, limit=100)

        # Filter unprocessed articles (no summary or importance_score)
        unprocessed = [a for a in articles if not a.summary or a.importance_score is None]

        logger.info(f"Found {len(unprocessed)} unprocessed articles")

        if not unprocessed:
            logger.info("No articles to process")
            return

        for article in unprocessed:
            try:
                logger.info(f"\nProcessing: {article.title[:60]}...")

                # 1. Generate summary if not exists
                if not article.summary:
                    logger.info("  - Generating summary...")
                    summary = with_retry(
                        lambda a=article: summarize_article(
                            title=a.title,
                            content=a.content or "",
                        ),
                        max_attempts=3,
                    )
                    article.summary = summary
                    logger.info(f"  ✅ Summary: {summary[:80]}...")

                # 2. Evaluate importance if not exists
                if article.importance_score is None:
                    logger.info("  - Evaluating importance...")
                    score = with_retry(
                        lambda a=article: evaluate_importance(
                            title=a.title,
                            content=a.content or a.summary or "",
                        ),
                        max_attempts=3,
                    )
                    article.importance_score = score
                    logger.info(f"  ✅ Importance score: {score:.2f}")

                # 3. Classify article type if category not set
                if not article.category:
                    logger.info("  - Classifying article...")
                    category = with_retry(
                        lambda a=article: classify_article_type(
                            title=a.title,
                            content=a.content or a.summary or "",
                        ),
                        max_attempts=3,
                    )
                    article.category = category
                    logger.info(f"  ✅ Category: {category}")

                # 4. Generate embedding and store in Vector DB
                if not article.vector_id:
                    logger.info("  - Generating embedding...")
                    try:
                        _ = with_retry(
                            lambda a=article: generate_embedding(
                                text=f"{a.title}\n\n{a.summary or a.content or ''}",
                            ),
                            max_attempts=3,
                        )

                        # Store in Qdrant
                        vector_id = str(article.id)
                        # TODO: Implement vector_db.upsert_article method
                        # For now, just set the vector_id
                        article.vector_id = vector_id
                        logger.info(f"  ✅ Generated embedding (Vector DB storage pending): {vector_id}")
                    except Exception as e:
                        logger.warning(
                            f"  ⚠️ Embedding generation failed: {e}. Skipping vector DB storage.",
                        )

                # Save updates
                crud.update_article(
                    db,
                    article.id,
                    summary=article.summary,
                    importance_score=article.importance_score,
                    category=article.category,
                    vector_id=article.vector_id,
                )

                processed_count += 1
                logger.info(f"✅ Processing completed for article {processed_count}")

            except Exception as e:
                logger.error(f"Error processing article '{article.title[:50]}': {e}")
                error_count += 1

        logger.info("\n" + "=" * 60)
        logger.info("✅ Article processing completed!")
        logger.info(f"Total processed: {processed_count} articles")
        logger.info(f"Errors: {error_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Fatal error in article processing task: {e}", exc_info=True)
    finally:
        db.close()


def send_digest_task() -> None:
    """
    Scheduled task for sending email digests to users.

    For each user:
    1. Get top N articles based on importance and preferences
    2. Build HTML email digest
    3. Send email
    4. Record in sent_digests table

    Runs daily at 08:00 KST (configurable per user)
    """
    logger.info("=" * 60)
    logger.info("Starting email digest task...")
    logger.info(f"Timestamp: {datetime.now(UTC).isoformat()}")
    logger.info("=" * 60)

    db = SessionLocal()
    sent_count = 0
    error_count = 0

    try:
        # Get all users with email enabled
        users = crud.list_users(db)
        logger.info(f"Found {len(users)} users")

        for user in users:
            try:
                # Get user preferences
                pref = crud.get_user_preference(db, user.id)
                if not pref or not pref.email_enabled:
                    logger.info(f"Email disabled for user: {user.email}")
                    continue

                logger.info(f"\nPreparing digest for: {user.email}")

                # Get articles from last 24 hours
                since = datetime.now(UTC) - timedelta(days=1)
                recent_articles = crud.get_top_articles_by_importance(
                    db,
                    limit=pref.daily_limit,
                    since=since,
                )

                if not recent_articles:
                    logger.info("  No articles to send")
                    continue

                logger.info(f"  Selected {len(recent_articles)} articles")

                # Send digest email
                success = send_daily_digest(
                    user_email=user.email,
                    user_name=user.name or user.email.split("@")[0],
                    articles=recent_articles,
                )

                if success:
                    # Record in database
                    crud.create_digest(
                        db=db,
                        user_id=user.id,
                        article_ids=[str(a.id) for a in recent_articles],
                    )
                    sent_count += 1
                    logger.info("  ✅ Email sent successfully")
                else:
                    logger.error("  ❌ Failed to send email")
                    error_count += 1

            except Exception as e:
                logger.error(f"Error sending digest to {user.email}: {e}")
                error_count += 1

        logger.info("\n" + "=" * 60)
        logger.info("✅ Email digest task completed!")
        logger.info(f"Emails sent: {sent_count}")
        logger.info(f"Errors: {error_count}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Fatal error in email digest task: {e}", exc_info=True)
    finally:
        db.close()
