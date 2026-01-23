"""관리자 페이지용 DB 헬퍼 함수."""

from sqlalchemy import func, select

from app.db.models import Feedback, SentDigest, User
from app.db.session import get_db


def get_total_user_count() -> int:
    """전체 사용자 수를 반환한다."""
    db = next(get_db())
    try:
        result = db.execute(select(func.count(User.id)))
        return result.scalar_one()
    finally:
        db.close()


def get_total_digest_count() -> int:
    """발송된 다이제스트 총 개수를 반환한다."""
    db = next(get_db())
    try:
        result = db.execute(select(func.count(SentDigest.id)))
        return result.scalar_one()
    finally:
        db.close()


def get_total_feedback_count() -> int:
    """전체 피드백 수를 반환한다."""
    db = next(get_db())
    try:
        result = db.execute(select(func.count(Feedback.id)))
        return result.scalar_one()
    finally:
        db.close()


def get_all_users_with_stats() -> list[dict]:
    """모든 사용자와 통계를 반환한다."""
    db = next(get_db())
    try:
        # 사용자 기본 정보 조회
        stmt = select(User).order_by(User.created_at.desc())
        result = db.execute(stmt)
        users = result.scalars().all()

        # 사용자별 통계 계산
        user_list = []
        for user in users:
            # 다이제스트 수
            digest_stmt = select(func.count(SentDigest.id)).where(SentDigest.user_id == user.id)
            digest_count = db.execute(digest_stmt).scalar_one()

            # 피드백 수
            feedback_stmt = select(func.count(Feedback.id)).where(Feedback.user_id == user.id)
            feedback_count = db.execute(feedback_stmt).scalar_one()

            user_list.append(
                {
                    "id": str(user.id),
                    "email": user.email,
                    "name": user.name or "N/A",
                    "created_at": user.created_at.isoformat(),
                    "last_login": user.last_login.isoformat() if user.last_login else None,
                    "digest_count": digest_count,
                    "feedback_count": feedback_count,
                },
            )

        return user_list
    finally:
        db.close()


def get_all_digests() -> list[dict]:
    """사용자 정보 포함 다이제스트 목록을 반환한다."""
    db = next(get_db())
    try:
        stmt = (
            select(SentDigest, User.email, User.name)
            .join(User, SentDigest.user_id == User.id)
            .order_by(SentDigest.sent_at.desc())
            .limit(100)  # 최근 100개로 제한
        )

        result = db.execute(stmt)
        rows = result.all()

        return [
            {
                "id": str(row.SentDigest.id),
                "user_id": str(row.SentDigest.user_id),
                "user_email": row.email,
                "user_name": row.name or "N/A",
                "article_ids": row.SentDigest.article_ids or [],
                "sent_at": row.SentDigest.sent_at.isoformat(),
                "email_opened": row.SentDigest.email_opened,
                "opened_at": (
                    row.SentDigest.opened_at.isoformat() if row.SentDigest.opened_at else None
                ),
            }
            for row in rows
        ]
    finally:
        db.close()
