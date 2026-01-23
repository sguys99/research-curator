"""사용자 CRUD 작업."""

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
    ID로 사용자를 조회한다.

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 UUID

    Returns:
        User 객체 또는 None
    """
    stmt = select(User).where(User.id == user_id)
    return db.scalar(stmt)


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    이메일로 사용자를 조회한다.

    Args:
        db: 데이터베이스 세션
        email: 사용자 이메일

    Returns:
        User 객체 또는 None
    """
    stmt = select(User).where(User.email == email)
    return db.scalar(stmt)


def create_user(db: Session, email: str, name: str | None = None) -> User:
    """
    새 사용자를 생성한다.

    Args:
        db: 데이터베이스 세션
        email: 사용자 이메일
        name: 사용자 이름(선택)

    Returns:
        생성된 User 객체
    """
    user = User(email=email, name=name)
    db.add(user)
    _commit_or_rollback(db)
    db.refresh(user)

    # 사용자 기본 선호도 생성
    preference = UserPreference(user_id=user.id)
    db.add(preference)
    _commit_or_rollback(db)

    return user


def update_user_last_login(db: Session, user_id: UUID) -> User | None:
    """
    사용자의 마지막 로그인 시간을 갱신한다.

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 UUID

    Returns:
        업데이트된 User 객체 또는 None
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
    사용자 정보를 업데이트한다.

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 UUID
        email: 새 이메일(선택)
        name: 새 이름(선택)

    Returns:
        업데이트된 User 객체 또는 None
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
    사용자를 삭제한다(CASCADE로 연관 데이터 삭제).

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 UUID

    Returns:
        삭제 성공 시 True, 미존재 시 False
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
    페이지네이션으로 사용자 목록을 조회한다.

    Args:
        db: 데이터베이스 세션
        skip: 건너뛸 레코드 수
        limit: 반환할 최대 레코드 수

    Returns:
        User 객체 목록
    """
    stmt = select(User).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())
