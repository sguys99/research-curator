"""Scheduled tasks for data collection, processing, and email sending."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

import nest_asyncio

from app.collectors.arxiv import ArxivCollector
from app.collectors.news import NewsCollector
from app.core.retry import with_retry
from app.db import crud
from app.db.session import SessionLocal
from app.email.builder import EmailBuilder
from app.email.selection import select_articles_for_user
from app.email.sender import EmailSender
from app.processors.classifier import ContentClassifier
from app.processors.embedder import TextEmbedder
from app.processors.evaluator import ImportanceEvaluator
from app.processors.summarizer import ArticleSummarizer

# Allow nested event loops
nest_asyncio.apply()

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
                    lambda f=field: asyncio.run(arxiv_collector.collect(query=f, limit=5)),
                    max_attempts=3,
                )

                for article_data in articles:
                    # Check if article already exists
                    existing = crud.get_article_by_url(db, article_data.url)
                    if existing:
                        continue

                    # Create article
                    crud.create_article(
                        db,
                        title=article_data.title,
                        content=article_data.content,
                        summary="",
                        source_url=article_data.url,
                        source_type="paper",
                        category="",
                        importance_score=0.5,
                        metadata=article_data.metadata,
                    )
                    collected_count += 1

            except Exception as e:
                logger.error(f"Error collecting from arXiv for field '{field}': {e}")
                error_count += 1

        # 2. Collect from News sources
        logger.info("\n2. Collecting from News sources...")
        news_collector = NewsCollector()

        for keyword in list(all_keywords)[:5]:  # Limit to 5 keywords to avoid rate limits
            try:
                articles = with_retry(
                    lambda k=keyword: asyncio.run(news_collector.collect(query=k, limit=3)),
                    max_attempts=3,
                )

                for article_data in articles:
                    existing = crud.get_article_by_url(db, article_data.url)
                    if existing:
                        continue

                    crud.create_article(
                        db,
                        title=article_data.title,
                        content=article_data.content,
                        summary="",
                        source_url=article_data.url,
                        source_type="news",
                        category="",
                        importance_score=0.5,
                        metadata=article_data.metadata,
                    )
                    collected_count += 1

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
                # 1. Generate summary if not exists
                if not article.summary:
                    summary = with_retry(
                        lambda a=article: summarize_article(
                            title=a.title,
                            content=a.content or "",
                        ),
                        max_attempts=3,
                    )
                    article.summary = summary

                # 2. Evaluate importance if not exists
                if article.importance_score is None:
                    score = with_retry(
                        lambda a=article: evaluate_importance(
                            title=a.title,
                            content=a.content or a.summary or "",
                        ),
                        max_attempts=3,
                    )
                    article.importance_score = score

                # 3. Classify article type if category not set
                if not article.category:
                    category = with_retry(
                        lambda a=article: classify_article_type(
                            title=a.title,
                            content=a.content or a.summary or "",
                        ),
                        max_attempts=3,
                    )
                    article.category = category

                # 4. Generate embedding and store in Vector DB
                if not article.vector_id:
                    try:
                        from app.vector_db.operations import VectorOperations

                        # Store in Qdrant (embedding is generated internally)
                        vector_ops = VectorOperations()
                        vector_id = asyncio.run(
                            vector_ops.insert_article(
                                article_id=str(article.id),
                                title=article.title,
                                content=article.content or "",
                                summary=article.summary or "",
                                source_type=article.source_type,
                                category=article.category or "general",
                                importance_score=article.importance_score or 0.5,
                                metadata=article.article_metadata or {},
                            ),
                        )

                        article.vector_id = vector_id
                        logger.info(f"Stored article in Qdrant with vector_id={vector_id}")

                    except Exception as e:
                        logger.warning(f"Embedding generation or Qdrant storage failed: {e}")
                        # Don't fail the entire processing, just log and continue

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

        # Get all articles from last 24 hours (fetch once for efficiency)
        since = datetime.now(UTC) - timedelta(days=1)
        all_articles = crud.get_articles_since(db, since=since)

        # Filter for fully processed articles only
        processed_articles = [
            a
            for a in all_articles
            if (
                # Must have summary OR category (LLM generated)
                (a.summary and a.summary.strip()) or (a.category and a.category.strip())
            )
            and (
                # Must have importance score processed (>= 0.1 threshold)
                a.importance_score is not None and a.importance_score >= 0.1
            )
        ]

        logger.info(
            f"Found {len(all_articles)} articles from last 24 hours, "
            f"{len(processed_articles)} are fully processed",
        )

        # Use processed articles instead of all articles
        all_articles = processed_articles

        if not all_articles:
            logger.warning(
                "No processed articles available for digest. "
                "This may happen if collection ran but processing hasn't completed yet. "
                "Skipping digest sending for now.",
            )
            return

        for user in users:
            try:
                # Get user preferences
                pref = crud.get_user_preference(db, user.id)
                if not pref or not pref.email_enabled:
                    continue

                # Select personalized articles based on user preferences
                personalized_articles = select_articles_for_user(
                    articles=all_articles,
                    preferences=pref,
                    limit=pref.daily_limit,
                )

                if not personalized_articles:
                    logger.info(f"No matching articles for {user.email}")
                    continue

                logger.info(
                    f"Selected {len(personalized_articles)} articles for "
                    f"{user.email} (keywords: {pref.keywords}, "
                    f"fields: {pref.research_fields})",
                )

                # Build and send digest email
                try:
                    # Build email content
                    builder = EmailBuilder()
                    html_content = builder.build_daily_digest(
                        user_name=user.name or user.email.split("@")[0],
                        user_email=user.email,
                        articles=personalized_articles,
                        daily_limit=pref.daily_limit,
                    )

                    # Generate subject
                    date_str = datetime.now().strftime("%Y년 %m월 %d일")
                    subject = f"🔬 Research Curator - {date_str} AI 연구 동향"

                    # Send email
                    sender = EmailSender()
                    asyncio.run(
                        sender.send_email(
                            to_email=user.email,
                            subject=subject,
                            html_content=html_content,
                        ),
                    )

                    # Record in database
                    crud.create_digest(
                        db=db,
                        user_id=user.id,
                        article_ids=[str(a.id) for a in personalized_articles],
                    )
                    sent_count += 1

                except Exception as email_error:
                    logger.error(f"Failed to send email to {user.email}: {email_error}")
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
