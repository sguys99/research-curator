"""CRUD operations package."""

from app.db.crud.articles import (
    count_articles,
    create_article,
    delete_article,
    get_article_by_id,
    get_article_by_url,
    get_article_statistics,
    get_articles,
    get_articles_by_ids,
    get_articles_since,
    get_top_articles_by_importance,
    list_articles,
    search_articles,
    update_article,
)
from app.db.crud.digests import (
    create_digest,
    get_digest_by_id,
    get_latest_digest,
    get_user_digests,
    get_user_sent_article_ids,
    list_user_digests,
    update_digest_opened,
)
from app.db.crud.feedback import (
    create_feedback,
    delete_feedback,
    get_article_average_rating,
    get_article_feedback,
    get_article_feedback_stats,
    get_feedback_by_id,
    get_user_feedback,
    get_user_feedback_for_article,
    list_article_feedbacks,
    list_user_feedbacks,
    update_feedback,
)
from app.db.crud.preferences import (
    create_user_preference,
    get_user_preference,
    update_user_preference,
)
from app.db.crud.users import (
    create_user,
    delete_user,
    get_user_by_email,
    get_user_by_id,
    list_users,
    update_user,
    update_user_last_login,
)

__all__ = [
    # Users
    "get_user_by_id",
    "get_user_by_email",
    "create_user",
    "update_user_last_login",
    "update_user",
    "delete_user",
    "list_users",
    # Preferences
    "get_user_preference",
    "create_user_preference",
    "update_user_preference",
    # Digests
    "get_user_digests",
    "get_latest_digest",
    "create_digest",
    "get_digest_by_id",
    "update_digest_opened",
    "list_user_digests",
    "get_user_sent_article_ids",
    # Articles
    "get_articles",
    "get_article_by_id",
    "get_article_by_url",
    "get_articles_by_ids",
    "get_articles_since",
    "create_article",
    "update_article",
    "delete_article",
    "get_article_statistics",
    "search_articles",
    "list_articles",
    "count_articles",
    "get_top_articles_by_importance",
    # Feedback
    "get_feedback_by_id",
    "get_user_feedback",
    "get_article_feedback",
    "create_feedback",
    "update_feedback",
    "delete_feedback",
    "get_article_feedback_stats",
    "get_user_feedback_for_article",
    "list_article_feedbacks",
    "list_user_feedbacks",
    "get_article_average_rating",
]
