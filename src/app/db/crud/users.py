"""CRUD operations for users."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User, UserPreference


def _commit_or_rollback(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_user_by_id(db: Session, user_id: UUID) -> User | None:
    """
    Get user by ID.

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        User object or None if not found
    """
    stmt = select(User).where(User.id == user_id)
    return db.scalar(stmt)


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Get user by email address.

    Args:
        db: Database session
        email: User email

    Returns:
        User object or None if not found
    """
    stmt = select(User).where(User.email == email)
    return db.scalar(stmt)


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
    _commit_or_rollback(db)
    db.refresh(user)

    # Create default preferences for the user
    preference = UserPreference(user_id=user.id)
    db.add(preference)
    _commit_or_rollback(db)

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
        _commit_or_rollback(db)
        db.refresh(user)
    return user


def update_user(
    db: Session,
    user_id: UUID,
    email: str | None = None,
    name: str | None = None,
) -> User | None:
    """
    Update user information.

    Args:
        db: Database session
        user_id: User UUID
        email: New email (optional)
        name: New name (optional)

    Returns:
        Updated User object or None if not found
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    if email is not None:
        user.email = email
    if name is not None:
        user.name = name

    _commit_or_rollback(db)
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: UUID) -> bool:
    """
    Delete user (CASCADE will delete related data).

    Args:
        db: Database session
        user_id: User UUID

    Returns:
        True if deleted, False if not found
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return False

    db.delete(user)
    _commit_or_rollback(db)
    return True


def list_users(
    db: Session,
    skip: int = 0,
    limit: int = 20,
) -> list[User]:
    """
    List all users with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of User objects
    """
    stmt = select(User).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())
