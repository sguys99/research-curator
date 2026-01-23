"""사용자 선호도 CRUD 작업."""

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
    사용자 ID로 선호도를 조회한다.

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 UUID

    Returns:
        UserPreference 객체 또는 None
    """
    stmt = select(UserPreference).where(UserPreference.user_id == user_id)
    return db.scalar(stmt)


def create_user_preference(
    db: Session,
    user_id: UUID,
    **kwargs: Any,
) -> UserPreference:
    """
    사용자 선호도를 생성한다.

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 UUID
        **kwargs: 선호도 필드

    Returns:
        생성된 UserPreference 객체
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
    사용자 선호도를 업데이트한다.

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 UUID
        **kwargs: 업데이트할 필드

    Returns:
        업데이트된 UserPreference 객체 또는 None
    """
    preference = get_user_preference(db, user_id)
    if not preference:
        return None

    # 필드 업데이트
    for key, value in kwargs.items():
        if value is not None and hasattr(preference, key):
            setattr(preference, key, value)

    _commit_or_rollback(db)
    db.refresh(preference)
    return preference
