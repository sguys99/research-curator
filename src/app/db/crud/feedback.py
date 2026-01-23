"""피드백 CRUD 작업."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import desc, func, select
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
    ID로 피드백을 조회한다.

    Args:
        db: 데이터베이스 세션
        feedback_id: 피드백 UUID

    Returns:
        Feedback 객체 또는 None
    """
    stmt = select(Feedback).where(Feedback.id == feedback_id)
    return db.scalar(stmt)


def get_user_feedback(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Feedback], int]:
    """
    페이지네이션으로 사용자 피드백을 조회한다.

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 UUID
        skip: 건너뛸 레코드 수
        limit: 반환할 최대 레코드 수

    Returns:
        (피드백 목록, 총 개수)
    """
    total_stmt = select(func.count()).select_from(Feedback).where(Feedback.user_id == user_id)
    total = db.scalar(total_stmt) or 0
    feedback_stmt = (
        select(Feedback)
        .where(Feedback.user_id == user_id)
        .order_by(desc(Feedback.created_at))
        .offset(skip)
        .limit(limit)
    )
    feedback_list = list(db.scalars(feedback_stmt).all())

    return feedback_list, total


def get_article_feedback(
    db: Session,
    article_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Feedback], int]:
    """
    특정 아티클의 피드백을 조회한다.

    Args:
        db: 데이터베이스 세션
        article_id: 아티클 UUID
        skip: 건너뛸 레코드 수
        limit: 반환할 최대 레코드 수

    Returns:
        (피드백 목록, 총 개수)
    """
    total_stmt = select(func.count()).select_from(Feedback).where(Feedback.article_id == article_id)
    total = db.scalar(total_stmt) or 0
    feedback_stmt = (
        select(Feedback)
        .where(Feedback.article_id == article_id)
        .order_by(desc(Feedback.created_at))
        .offset(skip)
        .limit(limit)
    )
    feedback_list = list(db.scalars(feedback_stmt).all())

    return feedback_list, total


def create_feedback(
    db: Session,
    user_id: UUID,
    article_id: UUID,
    rating: int,
    comment: str | None = None,
) -> Feedback:
    """
    새 피드백을 생성한다.

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 UUID
        article_id: 아티클 UUID
        rating: 평점(1-5)
        comment: 선택적 코멘트

    Returns:
        생성된 Feedback 객체
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
    피드백을 업데이트한다.

    Args:
        db: 데이터베이스 세션
        feedback_id: 피드백 UUID
        rating: 새 평점(선택)
        comment: 새 코멘트(선택)

    Returns:
        업데이트된 Feedback 객체 또는 None
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
    피드백을 삭제한다.

    Args:
        db: 데이터베이스 세션
        feedback_id: 피드백 UUID

    Returns:
        삭제 성공 시 True, 미존재 시 False
    """
    feedback = get_feedback_by_id(db, feedback_id)
    if not feedback:
        return False

    db.delete(feedback)
    _commit_or_rollback(db)
    return True


def get_article_feedback_stats(db: Session, article_id: UUID) -> dict:
    """
    아티클의 피드백 통계를 조회한다.

    Args:
        db: 데이터베이스 세션
        article_id: 아티클 UUID

    Returns:
        통계 딕셔너리(count, average_rating, rating_distribution)
    """
    feedback_stmt = select(Feedback).where(Feedback.article_id == article_id)
    feedback_list = list(db.scalars(feedback_stmt).all())

    if not feedback_list:
        return {
            "count": 0,
            "average_rating": 0.0,
            "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
        }

    # 통계 계산
    total_count = len(feedback_list)
    total_rating = sum(f.rating for f in feedback_list)
    average_rating = total_rating / total_count if total_count > 0 else 0.0

    # 평점 분포
    rating_counts_stmt = (
        select(Feedback.rating, func.count(Feedback.id))
        .where(Feedback.article_id == article_id)
        .group_by(Feedback.rating)
    )
    rating_counts = db.execute(rating_counts_stmt).all()

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
    특정 사용자/아티클의 피드백을 조회한다.

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 UUID
        article_id: 아티클 UUID

    Returns:
        Feedback 객체 또는 None
    """
    stmt = select(Feedback).where(
        Feedback.user_id == user_id,
        Feedback.article_id == article_id,
    )
    return db.scalar(stmt)


def list_article_feedbacks(
    db: Session,
    article_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> list[Feedback]:
    """
    아티클의 피드백 목록을 조회한다(간단 버전).

    Args:
        db: 데이터베이스 세션
        article_id: 아티클 UUID
        skip: 건너뛸 레코드 수
        limit: 반환할 최대 레코드 수

    Returns:
        Feedback 객체 목록
    """
    stmt = (
        select(Feedback)
        .where(Feedback.article_id == article_id)
        .order_by(desc(Feedback.created_at))
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def list_user_feedbacks(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> list[Feedback]:
    """
    사용자 피드백 목록을 조회한다(간단 버전).

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 UUID
        skip: 건너뛸 레코드 수
        limit: 반환할 최대 레코드 수

    Returns:
        Feedback 객체 목록
    """
    stmt = (
        select(Feedback)
        .where(Feedback.user_id == user_id)
        .order_by(desc(Feedback.created_at))
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def get_article_average_rating(
    db: Session,
    article_id: UUID,
) -> float | None:
    """
    아티클의 평균 평점을 계산한다.

    Args:
        db: 데이터베이스 세션
        article_id: 아티클 UUID

    Returns:
        평균 평점(float) 또는 None
    """
    stats = get_article_feedback_stats(db, article_id)
    if stats["count"] == 0:
        return None
    return stats["average_rating"]
