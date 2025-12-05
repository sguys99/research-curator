"""CRUD operations package."""

from app.db.crud.articles import (
    create_article,
    delete_article,
    get_article_by_id,
    get_article_by_url,
    get_article_statistics,
    get_articles,
    get_articles_by_ids,
    search_articles,
    update_article,
)
from app.db.crud.digests import create_digest, get_latest_digest, get_user_digests
from app.db.crud.feedback import (
    create_feedback,
    delete_feedback,
    get_article_feedback,
    get_article_feedback_stats,
    get_feedback_by_id,
    get_user_feedback,
    update_feedback,
)
from app.db.crud.preferences import (
    create_user_preference,
    get_user_preference,
    update_user_preference,
)
from app.db.crud.users import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user_last_login,
)

__all__ = [
    # Users
    "get_user_by_id",
    "get_user_by_email",
    "create_user",
    "update_user_last_login",
    # Preferences
    "get_user_preference",
    "create_user_preference",
    "update_user_preference",
    # Digests
    "get_user_digests",
    "get_latest_digest",
    "create_digest",
    # Articles
    "get_articles",
    "get_article_by_id",
    "get_article_by_url",
    "get_articles_by_ids",
    "create_article",
    "update_article",
    "delete_article",
    "get_article_statistics",
    "search_articles",
    # Feedback
    "get_feedback_by_id",
    "get_user_feedback",
    "get_article_feedback",
    "create_feedback",
    "update_feedback",
    "delete_feedback",
    "get_article_feedback_stats",
]
