"""CRUD operations for user preferences."""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import UserPreference


def _commit_or_rollback(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_user_preference(db: Session, user_id: UUID) -> UserPreference | None:
    """
    Get user preferences by user ID.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        UserPreference object or None if not found
    """
    stmt = select(UserPreference).where(UserPreference.user_id == user_id)
    return db.scalar(stmt)


def create_user_preference(
    db: Session,
    user_id: UUID,
    **kwargs: Any,
) -> UserPreference:
    """
    Create user preferences.

    Args:
        db: Database session
        user_id: User UUID
        **kwargs: Preference fields

    Returns:
        Created UserPreference object
    """
    preference = UserPreference(user_id=user_id, **kwargs)
    db.add(preference)
    _commit_or_rollback(db)
    db.refresh(preference)
    return preference


def update_user_preference(
    db: Session,
    user_id: UUID,
    **kwargs: Any,
) -> UserPreference | None:
    """
    Update user preferences.

    Args:
        db: Database session
        user_id: User UUID
        **kwargs: Fields to update

    Returns:
        Updated UserPreference object or None if not found
    """
    preference = get_user_preference(db, user_id)
    if not preference:
        return None

    # Update fields
    for key, value in kwargs.items():
        if value is not None and hasattr(preference, key):
            setattr(preference, key, value)

    _commit_or_rollback(db)
    db.refresh(preference)
    return preference
