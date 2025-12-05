"""CRUD operations for user preferences."""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import UserPreference


def get_user_preference(db: Session, user_id: UUID) -> UserPreference | None:
    """
    Get user preferences by user ID.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        UserPreference object or None if not found
    """
    return db.query(UserPreference).filter(UserPreference.user_id == user_id).first()


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
    db.commit()
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

    db.commit()
    db.refresh(preference)
    return preference
