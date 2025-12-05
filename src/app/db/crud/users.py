"""CRUD operations for users."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models import User, UserPreference


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    """
    Get user by ID.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        User object or None if not found
    """
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Get user by email address.

    Args:
        db: Database session
        email: User email

    Returns:
        User object or None if not found
    """
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, email: str, name: str | None = None) -> User:
    """
    Create a new user.

    Args:
        db: Database session
        email: User email
        name: User name (optional)

    Returns:
        Created User object
    """
    user = User(email=email, name=name)
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create default preferences for the user
    preference = UserPreference(user_id=user.id)
    db.add(preference)
    db.commit()

    return user


def update_user_last_login(db: Session, user_id: UUID) -> User | None:
    """
    Update user's last login timestamp.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        Updated User object or None if not found
    """
    user = get_user_by_id(db, user_id)
    if user:
        user.last_login = datetime.now(UTC)
        db.commit()
        db.refresh(user)
    return user
