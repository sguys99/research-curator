"""CRUD operations for feedback."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.models import Feedback


def _commit_or_rollback(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_feedback_by_id(db: Session, feedback_id: UUID) -> Feedback | None:
    """
    Get feedback by ID.

    Args:
        db: Database session
        feedback_id: Feedback UUID

    Returns:
        Feedback object or None if not found
    """
    return db.query(Feedback).filter(Feedback.id == feedback_id).first()


def get_user_feedback(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Feedback], int]:
    """
    Get user's feedback with pagination.

    Args:
        db: Database session
        user_id: User UUID
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        Tuple of (feedback list, total count)
    """
    query = db.query(Feedback).filter(Feedback.user_id == user_id)

    total = query.count()
    feedback_list = query.order_by(desc(Feedback.created_at)).offset(skip).limit(limit).all()

    return feedback_list, total


def get_article_feedback(
    db: Session,
    article_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Feedback], int]:
    """
    Get feedback for a specific article.

    Args:
        db: Database session
        article_id: Article UUID
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        Tuple of (feedback list, total count)
    """
    query = db.query(Feedback).filter(Feedback.article_id == article_id)

    total = query.count()
    feedback_list = query.order_by(desc(Feedback.created_at)).offset(skip).limit(limit).all()

    return feedback_list, total


def create_feedback(
    db: Session,
    user_id: UUID,
    article_id: UUID,
    rating: int,
    comment: str | None = None,
) -> Feedback:
    """
    Create new feedback.

    Args:
        db: Database session
        user_id: User UUID
        article_id: Article UUID
        rating: Rating (1-5)
        comment: Optional comment text

    Returns:
        Created Feedback object
    """
    feedback = Feedback(
        user_id=user_id,
        article_id=article_id,
        rating=rating,
        comment=comment,
        created_at=datetime.now(UTC),
    )
    db.add(feedback)
    _commit_or_rollback(db)
    db.refresh(feedback)
    return feedback


def update_feedback(
    db: Session,
    feedback_id: UUID,
    rating: int | None = None,
    comment: str | None = None,
) -> Feedback | None:
    """
    Update feedback.

    Args:
        db: Database session
        feedback_id: Feedback UUID
        rating: New rating (optional)
        comment: New comment (optional)

    Returns:
        Updated Feedback object or None if not found
    """
    feedback = get_feedback_by_id(db, feedback_id)
    if not feedback:
        return None

    if rating is not None:
        feedback.rating = rating
    if comment is not None:
        feedback.comment = comment

    _commit_or_rollback(db)
    db.refresh(feedback)
    return feedback


def delete_feedback(db: Session, feedback_id: UUID) -> bool:
    """
    Delete feedback.

    Args:
        db: Database session
        feedback_id: Feedback UUID

    Returns:
        True if deleted, False if not found
    """
    feedback = get_feedback_by_id(db, feedback_id)
    if not feedback:
        return False

    db.delete(feedback)
    _commit_or_rollback(db)
    return True


def get_article_feedback_stats(db: Session, article_id: UUID) -> dict:
    """
    Get feedback statistics for an article.

    Args:
        db: Database session
        article_id: Article UUID

    Returns:
        Dictionary with statistics (count, average_rating, rating_distribution)
    """
    from sqlalchemy import func

    feedback_list = db.query(Feedback).filter(Feedback.article_id == article_id).all()

    if not feedback_list:
        return {
            "count": 0,
            "average_rating": 0.0,
            "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        }

    # Calculate statistics
    total_count = len(feedback_list)
    total_rating = sum(f.rating for f in feedback_list)
    average_rating = total_rating / total_count if total_count > 0 else 0.0

    # Rating distribution
    rating_counts = (
        db.query(Feedback.rating, func.count(Feedback.id))
        .filter(Feedback.article_id == article_id)
        .group_by(Feedback.rating)
        .all()
    )

    rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for rating, count in rating_counts:
        rating_distribution[rating] = count

    return {
        "count": total_count,
        "average_rating": round(average_rating, 2),
        "rating_distribution": rating_distribution,
    }


def get_user_feedback_for_article(
    db: Session,
    user_id: UUID,
    article_id: UUID,
) -> Feedback | None:
    """
    Get specific user's feedback for a specific article.

    Args:
        db: Database session
        user_id: User UUID
        article_id: Article UUID

    Returns:
        Feedback object or None if not found
    """
    return (
        db.query(Feedback).filter(Feedback.user_id == user_id, Feedback.article_id == article_id).first()
    )


def list_article_feedbacks(
    db: Session,
    article_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> list[Feedback]:
    """
    List feedbacks for an article (simplified version).

    Args:
        db: Database session
        article_id: Article UUID
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of Feedback objects
    """
    return (
        db.query(Feedback)
        .filter(Feedback.article_id == article_id)
        .order_by(desc(Feedback.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def list_user_feedbacks(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> list[Feedback]:
    """
    List user's feedbacks (simplified version).

    Args:
        db: Database session
        user_id: User UUID
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of Feedback objects
    """
    return (
        db.query(Feedback)
        .filter(Feedback.user_id == user_id)
        .order_by(desc(Feedback.created_at))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_article_average_rating(
    db: Session,
    article_id: UUID,
) -> float | None:
    """
    Calculate average rating for an article.

    Args:
        db: Database session
        article_id: Article UUID

    Returns:
        Average rating (float) or None if no ratings
    """
    stats = get_article_feedback_stats(db, article_id)
    if stats["count"] == 0:
        return None
    return stats["average_rating"]
