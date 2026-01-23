"""발송된 다이제스트 CRUD 작업."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import SentDigest


def _commit_or_rollback(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def get_user_digests(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 10,
) -> tuple[list[SentDigest], int]:
    """
    페이지네이션으로 사용자 다이제스트 기록을 조회한다.

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 UUID
        skip: 건너뛸 레코드 수
        limit: 반환할 최대 레코드 수

    Returns:
        (다이제스트 목록, 총 개수)
    """
    total_stmt = select(func.count()).select_from(SentDigest).where(SentDigest.user_id == user_id)
    total = db.scalar(total_stmt) or 0

    digests_stmt = (
        select(SentDigest)
        .where(SentDigest.user_id == user_id)
        .order_by(SentDigest.sent_at.desc())
        .offset(skip)
        .limit(limit)
    )
    digests = list(db.scalars(digests_stmt).all())

    return digests, total


def get_latest_digest(db: Session, user_id: UUID) -> SentDigest | None:
    """
    사용자의 최신 다이제스트를 조회한다.

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 UUID

    Returns:
        최신 SentDigest 객체 또는 None
    """
    stmt = (
        select(SentDigest)
        .where(SentDigest.user_id == user_id)
        .order_by(SentDigest.sent_at.desc())
        .limit(1)
    )
    return db.scalar(stmt)


def create_digest(
    db: Session,
    user_id: UUID,
    article_ids: list[str],
) -> SentDigest:
    """
    새로운 다이제스트 레코드를 생성한다.

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 UUID
        article_ids: 다이제스트에 포함된 아티클 ID 목록

    Returns:
        생성된 SentDigest 객체
    """
    digest = SentDigest(user_id=user_id, article_ids=article_ids)
    db.add(digest)
    _commit_or_rollback(db)
    db.refresh(digest)
    return digest


def get_digest_by_id(db: Session, digest_id: UUID) -> SentDigest | None:
    """
    ID로 다이제스트를 조회한다.

    Args:
        db: 데이터베이스 세션
        digest_id: 다이제스트 UUID

    Returns:
        SentDigest 객체 또는 None
    """
    stmt = select(SentDigest).where(SentDigest.id == digest_id)
    return db.scalar(stmt)


def update_digest_opened(
    db: Session,
    digest_id: UUID,
    opened_at,
) -> SentDigest | None:
    """
    다이제스트를 열림 상태로 표시하고 시각을 기록한다.

    Args:
        db: 데이터베이스 세션
        digest_id: 다이제스트 UUID
        opened_at: 열람 시각

    Returns:
        업데이트된 SentDigest 객체 또는 None
    """
    digest = get_digest_by_id(db, digest_id)
    if not digest:
        return None

    digest.email_opened = True
    digest.opened_at = opened_at
    _commit_or_rollback(db)
    db.refresh(digest)
    return digest


def list_user_digests(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 10,
) -> list[SentDigest]:
    """
    사용자 다이제스트 목록을 조회한다(get_user_digests의 간단 버전).

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 UUID
        skip: 건너뛸 레코드 수
        limit: 반환할 최대 레코드 수

    Returns:
        SentDigest 객체 목록
    """
    stmt = (
        select(SentDigest)
        .where(SentDigest.user_id == user_id)
        .order_by(SentDigest.sent_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def has_digest_sent_today(db: Session, user_id: UUID) -> bool:
    """
    오늘(UTC 기준) 이미 다이제스트가 발송되었는지 확인한다.

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 UUID

    Returns:
        오늘 발송되었으면 True, 아니면 False
    """
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)

    stmt = select(SentDigest).where(
        SentDigest.user_id == user_id,
        SentDigest.sent_at >= today_start,
    )
    digest = db.scalar(stmt)

    return digest is not None


def get_user_sent_article_ids(
    db: Session,
    user_id: UUID,
    days: int = 7,
) -> set[str]:
    """
    최근 N일 동안 사용자에게 발송된 아티클 ID를 조회한다.

    지정 기간 내에 발송된 아티클 ID를 모두 가져와 중복 발송을 방지한다.

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 UUID
        days: 조회할 기간(일, 기본값: 7)

    Returns:
        최근 N일 동안 발송된 아티클 ID 집합(문자열)

    Examples:
        >>> sent_ids = get_user_sent_article_ids(db, user_id, days=7)
        >>> # 이미 보낸 아티클 제외
        >>> new_articles = [a for a in articles if str(a.id) not in sent_ids]
    """
    if days <= 0:
        return set()

    # 기준 시각 계산
    since = datetime.now(UTC) - timedelta(days=days)

    # 최근 N일 내 발송된 다이제스트 조회
    stmt = select(SentDigest).where(SentDigest.user_id == user_id, SentDigest.sent_at >= since)
    digests = list(db.scalars(stmt).all())

    # 다이제스트에서 아티클 ID 수집
    article_ids = set()
    for digest in digests:
        if digest.article_ids:
            article_ids.update(digest.article_ids)

    return article_ids
