"""Article selection and filtering logic for daily digests."""

import asyncio
import logging
from typing import Any

from app.db.models import CollectedArticle, UserPreference

logger = logging.getLogger(__name__)


# 사용자 선호도에 맞는 최적의 아티클을 선택하는 로직
def select_articles_for_user(
    articles: list[CollectedArticle],
    preferences: UserPreference,
    limit: int | None = None,
) -> list[CollectedArticle]:
    """Synchronous wrapper for async selection (for sync callers)."""
    return asyncio.run(select_articles_for_user_async(articles, preferences, limit))


async def select_articles_for_user_async(
    articles: list[CollectedArticle],
    preferences: UserPreference,
    limit: int | None = None,
) -> list[CollectedArticle]:
    """
    Select and filter articles based on user preferences.

    Strategy (updated with semantic search and fallback cascade):
    1. Try semantic search via Qdrant (if articles are vectorized)
    2. If semantic fails, try keyword/field filtering
    3. If that fails, try title-only matching
    4. If that fails, use importance ranking
    5. Apply category distribution
    6. Sort by importance score
    7. Select top N

    Args:
        articles: Available articles
        preferences: User preferences
        limit: Maximum articles to select (defaults to preferences.daily_limit)

    Returns:
        list[CollectedArticle]: Selected articles
    """
    if not articles:
        return []

    limit = limit or preferences.daily_limit or 5

    # Step 1: Try semantic search first (most powerful)
    filtered = await _semantic_filter(
        articles,
        preferences,
        limit=limit * 3,  # Get more candidates for distribution
        score_threshold=0.65,
    )

    if filtered:
        logger.info(f"Using semantic search: {len(filtered)} articles")
    else:
        logger.info("Semantic search yielded no results, trying keyword matching")

        # Step 2: Try traditional keyword/field filtering
        filtered = _filter_by_preferences(articles, preferences)

        if not filtered:
            logger.warning(
                f"No articles match user preferences for "
                f"keywords={preferences.keywords}, fields={preferences.research_fields}. "
                f"Trying fallback strategies.",
            )

            # Step 3: Fallback to title-only keyword matching
            filtered = _fallback_title_search(articles, preferences)

            if not filtered:
                logger.warning("Title fallback found nothing. Trying importance ranking.")

                # Step 4: Final fallback to importance ranking
                filtered = _fallback_importance_ranking(articles, limit=limit)

            if not filtered:
                logger.warning(
                    "All filtering strategies failed. Returning empty to avoid "
                    "sending identical digests to all users.",
                )
                return []

            logger.info(f"Fallback strategy succeeded with {len(filtered)} articles")

    # Step 5: Apply category distribution
    distributed = _apply_category_distribution(filtered, preferences)

    # Step 6: Sort by importance score
    sorted_articles = sorted(
        distributed,
        key=lambda x: x.importance_score or 0.0,
        reverse=True,
    )

    # Step 7: Select top N
    selected = sorted_articles[:limit]

    logger.info(
        f"Selected {len(selected)} articles from {len(articles)} available "
        f"(filtered: {len(filtered)}, distributed: {len(distributed)})",
    )

    return selected


def _filter_by_preferences(
    articles: list[CollectedArticle],
    preferences: UserPreference,
) -> list[CollectedArticle]:
    """
    Filter articles by user's research fields and keywords.

    Args:
        articles: Available articles
        preferences: User preferences

    Returns:
        list[CollectedArticle]: Filtered articles
    """
    keywords = preferences.keywords or []
    research_fields = preferences.research_fields or []

    if not keywords and not research_fields:
        return articles

    # First, filter out articles without sufficient metadata
    validated_articles = [a for a in articles if _has_sufficient_metadata(a)]

    if not validated_articles:
        logger.warning(
            f"No articles with sufficient metadata found. "
            f"Total articles: {len(articles)}, Validated: {len(validated_articles)}",
        )
        return []

    filtered = []

    for article in validated_articles:
        # Check if article matches keywords
        matches_keyword = False
        if keywords:
            # Include content field (first 500 chars) to handle articles with empty summaries
            article_text = (
                f"{article.title} {article.summary or ''} "
                f"{article.category or ''} {(article.content or '')[:500]}"
            )
            article_text_lower = article_text.lower()
            matches_keyword = any(kw.lower() in article_text_lower for kw in keywords)

        # Check if article matches research fields
        matches_field = False
        if research_fields:
            article_category = (article.category or "").lower()
            matches_field = any(field.lower() in article_category for field in research_fields)

        # Include article if it matches keywords OR research fields
        if matches_keyword or matches_field:
            filtered.append(article)

    return filtered


def _has_sufficient_metadata(article: CollectedArticle) -> bool:
    """
    Check if article has sufficient metadata for filtering.

    Args:
        article: Article to check

    Returns:
        True if article has been fully processed with LLM
    """
    # Article needs at least summary OR category to be considered processed
    # AND importance_score must be set (not None and not default 0.5)
    has_summary = bool(article.summary and article.summary.strip())
    has_category = bool(article.category and article.category.strip())
    has_score = article.importance_score is not None and article.importance_score != 0.5

    return (has_summary or has_category) and has_score


def _fallback_title_search(
    articles: list[CollectedArticle],
    preferences: UserPreference,
) -> list[CollectedArticle]:
    """
    Fallback: Match keywords against titles only when full filtering fails.

    This is more restrictive than full-text search but better than returning
    all articles.

    Args:
        articles: Available articles
        preferences: User preferences

    Returns:
        Articles matching keywords in title
    """
    keywords = preferences.keywords or []

    if not keywords:
        logger.info("No keywords for fallback search")
        return []

    matched = []
    for article in articles:
        if not _has_sufficient_metadata(article):
            continue

        title_lower = article.title.lower()
        if any(kw.lower() in title_lower for kw in keywords):
            matched.append(article)

    logger.info(f"Fallback title search found {len(matched)} articles " f"matching keywords: {keywords}")

    return matched


def _fallback_importance_ranking(
    articles: list[CollectedArticle],
    limit: int = 5,
) -> list[CollectedArticle]:
    """
    Last resort fallback: Select top articles by importance score.

    When all other strategies fail, return highest-rated articles
    that have been processed.

    Args:
        articles: Available articles
        limit: Maximum number to return

    Returns:
        Top articles by importance
    """
    # Only use validated articles
    validated = [a for a in articles if _has_sufficient_metadata(a)]

    if not validated:
        logger.warning("No validated articles for importance fallback")
        return []

    # Sort by importance score descending
    sorted_articles = sorted(
        validated,
        key=lambda x: x.importance_score or 0.0,
        reverse=True,
    )

    selected = sorted_articles[:limit]

    logger.info(
        f"Importance fallback selected {len(selected)} top articles "
        f"from {len(validated)} validated articles",
    )

    return selected


async def _generate_preference_embedding(preferences: UserPreference) -> list[float] | None:
    """
    Generate embedding from user preferences for semantic search.

    Combines research_fields and keywords into a single text and generates
    embedding.

    Args:
        preferences: User preferences

    Returns:
        Embedding vector or None if generation fails
    """
    # Build preference text from fields and keywords
    fields = preferences.research_fields or []
    keywords = preferences.keywords or []

    if not fields and not keywords:
        logger.warning("No fields or keywords to generate embedding from")
        return None

    # Combine into searchable text
    preference_text = "Research interests: " + ", ".join(fields)
    if keywords:
        preference_text += ". Keywords: " + ", ".join(keywords)

    logger.info(f"Generating embedding for preference text: {preference_text[:100]}...")

    try:
        from app.processors.embedder import TextEmbedder

        embedder = TextEmbedder()
        embedding = await embedder.embed(preference_text)
        logger.info(f"Generated preference embedding: {len(embedding)} dimensions")
        return embedding
    except Exception as e:
        logger.error(f"Failed to generate preference embedding: {e}")
        return None


async def _semantic_filter(
    articles: list[CollectedArticle],
    preferences: UserPreference,
    limit: int = 20,
    score_threshold: float = 0.65,
) -> list[CollectedArticle]:
    """
    Filter articles using semantic similarity search via Qdrant.

    Strategy:
    1. Generate embedding from user's research_fields + keywords
    2. Search Qdrant for semantically similar articles
    3. Filter results to only include articles from provided list
    4. Return top matches above threshold

    Args:
        articles: Available articles (should have vector_id set)
        preferences: User preferences
        limit: Max articles to return
        score_threshold: Minimum similarity score (0.0-1.0)

    Returns:
        Semantically matched articles ordered by relevance
    """
    try:
        # Generate preference embedding
        preference_embedding = await _generate_preference_embedding(preferences)

        if not preference_embedding:
            logger.warning("Could not generate preference embedding, skipping semantic search")
            return []

        # Get vector operations client
        from app.vector_db.operations import VectorOperations

        vector_ops = VectorOperations()

        # Filter articles that have vector_id (embedded in Qdrant)
        vectorized_articles = [a for a in articles if a.vector_id]

        if not vectorized_articles:
            logger.warning(
                f"No articles have vector_id set. " f"Total articles: {len(articles)}, Vectorized: 0",
            )
            return []

        logger.info(f"Performing semantic search on {len(vectorized_articles)} articles")

        # Search Qdrant with preference embedding
        search_results = vector_ops.qdrant_client.client.query_points(
            collection_name=vector_ops.collection_name,
            query=preference_embedding,
            limit=limit * 2,  # Get more results to filter
            score_threshold=score_threshold,
            with_payload=True,
            with_vectors=False,
        ).points

        # Create mapping of vector_id -> article
        article_map = {a.vector_id: a for a in vectorized_articles}

        # Filter results to only include our available articles
        matched_articles = []
        for hit in search_results:
            vector_id = str(hit.id)
            if vector_id in article_map:
                article = article_map[vector_id]
                # Store similarity score as temporary attribute for sorting
                article._semantic_score = hit.score  # noqa: SLF001
                matched_articles.append(article)

        # Sort by semantic score and limit
        matched_articles.sort(
            key=lambda x: getattr(x, "_semantic_score", 0.0),
            reverse=True,
        )
        matched_articles = matched_articles[:limit]

        logger.info(
            f"Semantic search found {len(matched_articles)} matches "
            f"above threshold {score_threshold}",
        )

        return matched_articles

    except Exception as e:
        logger.error(f"Semantic search failed: {e}", exc_info=True)
        return []


def _semantic_filter_sync(
    articles: list[CollectedArticle],
    preferences: UserPreference,
    limit: int = 20,
    score_threshold: float = 0.65,
) -> list[CollectedArticle]:
    """
    Synchronous wrapper for semantic filtering.

    This allows calling from sync code like select_articles_for_user.
    """
    try:
        return asyncio.run(_semantic_filter(articles, preferences, limit, score_threshold))
    except Exception as e:
        logger.error(f"Semantic filter sync wrapper failed: {e}")
        return []


def _apply_category_distribution(
    articles: list[CollectedArticle],
    preferences: UserPreference,
) -> list[CollectedArticle]:
    """
    Apply category distribution based on user preferences.

    Args:
        articles: Filtered articles
        preferences: User preferences with info_types

    Returns:
        list[CollectedArticle]: Articles with balanced category distribution
    """
    info_types = preferences.info_types or {}

    # Default distribution if not specified
    default_distribution = {"paper": 50, "news": 30, "report": 20}
    distribution = {**default_distribution, **info_types}

    # Normalize distribution to percentages
    total = sum(distribution.values())
    if total == 0:
        return articles

    normalized = {k: v / total for k, v in distribution.items()}

    # Group articles by type
    papers = [a for a in articles if a.source_type == "paper"]
    news = [a for a in articles if a.source_type == "news"]
    reports = [a for a in articles if a.source_type == "report"]

    # Calculate target counts
    total_articles = len(articles)
    target_paper = int(total_articles * normalized.get("paper", 0.5))
    target_news = int(total_articles * normalized.get("news", 0.3))
    target_report = int(total_articles * normalized.get("report", 0.2))

    # Select articles from each category
    selected = []
    selected.extend(_select_top_by_importance(papers, target_paper))
    selected.extend(_select_top_by_importance(news, target_news))
    selected.extend(_select_top_by_importance(reports, target_report))

    return selected


def _select_top_by_importance(articles: list[CollectedArticle], count: int) -> list[CollectedArticle]:
    """
    Select top N articles by importance score.

    Args:
        articles: Articles to select from
        count: Number to select

    Returns:
        list[CollectedArticle]: Top N articles
    """
    sorted_articles = sorted(articles, key=lambda x: x.importance_score or 0.0, reverse=True)
    return sorted_articles[:count]


def filter_by_date_range(
    articles: list[CollectedArticle],
    start_date: Any | None = None,
    end_date: Any | None = None,
) -> list[CollectedArticle]:
    """
    Filter articles by collection date range.

    Args:
        articles: Articles to filter
        start_date: Start date (inclusive)
        end_date: End date (inclusive)

    Returns:
        list[CollectedArticle]: Filtered articles
    """
    filtered = articles

    if start_date:
        filtered = [a for a in filtered if a.collected_at and a.collected_at >= start_date]

    if end_date:
        filtered = [a for a in filtered if a.collected_at and a.collected_at <= end_date]

    return filtered


def get_category_distribution(articles: list[CollectedArticle]) -> dict[str, int]:
    """
    Get distribution of articles by category.

    Args:
        articles: Articles to analyze

    Returns:
        dict: Category counts
    """
    distribution = {"paper": 0, "news": 0, "report": 0, "other": 0}

    for article in articles:
        category = article.source_type or "other"
        if category in distribution:
            distribution[category] += 1
        else:
            distribution["other"] += 1

    return distribution
