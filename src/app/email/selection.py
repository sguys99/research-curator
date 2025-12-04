"""Article selection and filtering logic for daily digests."""

import logging
from typing import Any

from app.db.models import CollectedArticle, UserPreference

logger = logging.getLogger(__name__)


def select_articles_for_user(
    articles: list[CollectedArticle],
    preferences: UserPreference,
    limit: int | None = None,
) -> list[CollectedArticle]:
    """
    Select and filter articles based on user preferences.

    Strategy:
    1. Filter by user's research fields and keywords
    2. Apply info_types distribution (paper/news/report ratio)
    3. Sort by importance score
    4. Select top N with category balancing

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

    # Step 1: Filter by keywords and fields
    filtered = _filter_by_preferences(articles, preferences)

    if not filtered:
        logger.warning("No articles match user preferences, using all articles")
        filtered = articles

    # Step 2: Apply category distribution
    distributed = _apply_category_distribution(filtered, preferences)

    # Step 3: Sort by importance
    sorted_articles = sorted(distributed, key=lambda x: x.importance_score or 0.0, reverse=True)

    # Step 4: Select top N
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

    filtered = []

    for article in articles:
        # Check if article matches keywords
        matches_keyword = False
        if keywords:
            article_text = f"{article.title} {article.summary or ''} {article.category or ''}"
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
