"""사용자 관리 및 선호도 설정을 위한 라우터."""

import logging
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.schemas.users import (
    DigestListResponse,
    DigestResponse,
    UserPreferenceResponse,
    UserPreferenceUpdate,
    UserResponse,
    UserUpdate,
)
from app.db.crud.digests import get_user_digests
from app.db.crud.preferences import get_user_preference, update_user_preference
from app.db.crud.users import update_user
from app.db.models import CollectedArticle, User
from app.db.session import get_db
from app.email.selection import select_articles_for_user_async

logger = logging.getLogger(__name__)

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    현재 인증된 사용자 정보를 조회한다.

    Args:
        current_user: JWT 토큰에서 추출된 사용자

    Returns:
        사용자 정보
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@router.put("/me", response_model=UserResponse)
def update_current_user(
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    현재 인증된 사용자 정보를 업데이트한다.

    Args:
        update_data: 업데이트할 사용자 데이터
        db: 데이터베이스 세션
        current_user: JWT 토큰에서 추출된 사용자

    Returns:
        업데이트된 사용자 정보

    Raises:
        HTTPException: 업데이트 실패 시
    """
    updated_user = update_user(
        db,
        current_user.id,
        **update_data.model_dump(exclude_unset=True),
    )

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=updated_user.id,
        email=updated_user.email,
        name=updated_user.name,
        created_at=updated_user.created_at,
        last_login=updated_user.last_login,
    )


@router.get("/{user_id}/preferences", response_model=UserPreferenceResponse)
def get_preferences(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserPreferenceResponse:
    """
    사용자 선호도를 조회한다.

    Args:
        user_id: 사용자 UUID
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        사용자 선호도

    Raises:
        HTTPException: 권한이 없거나 선호도를 찾지 못한 경우
    """
    # 권한 확인(사용자는 자신의 선호도만 조회 가능)
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access these preferences",
        )

    preference = get_user_preference(db, user_id)
    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found",
        )

    # sources가 리스트인지 확인(레거시 dict 포맷 대응)
    sources = preference.sources
    if isinstance(sources, dict):
        sources = []
    elif sources is None:
        sources = []

    return UserPreferenceResponse(
        id=preference.id,
        user_id=preference.user_id,
        research_fields=preference.research_fields or [],
        keywords=preference.keywords or [],
        sources=sources,
        info_types=preference.info_types or {},
        email_time=preference.email_time,
        daily_limit=preference.daily_limit,
        email_enabled=preference.email_enabled,
        created_at=preference.created_at,
        updated_at=preference.updated_at,
    )


@router.put("/{user_id}/preferences", response_model=UserPreferenceResponse)
def update_preferences(
    user_id: UUID,
    update_data: UserPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserPreferenceResponse:
    """
    사용자 선호도를 업데이트한다.

    Args:
        user_id: 사용자 UUID
        update_data: 선호도 업데이트 데이터
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        업데이트된 사용자 선호도

    Raises:
        HTTPException: 권한이 없거나 업데이트 실패 시
    """
    # 권한 확인
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update these preferences",
        )

    # 선호도 업데이트
    preference = update_user_preference(
        db,
        user_id,
        **update_data.model_dump(exclude_unset=True),
    )

    if not preference:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found",
        )

    return UserPreferenceResponse(
        id=preference.id,
        user_id=preference.user_id,
        research_fields=preference.research_fields,
        keywords=preference.keywords,
        sources=preference.sources,
        info_types=preference.info_types,
        email_time=preference.email_time,
        daily_limit=preference.daily_limit,
        email_enabled=preference.email_enabled,
        created_at=preference.created_at,
        updated_at=preference.updated_at,
    )


@router.get("/{user_id}/digests", response_model=DigestListResponse)
def get_digests(
    user_id: UUID,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DigestListResponse:
    """
    사용자의 다이제스트 기록을 조회한다.

    Args:
        user_id: 사용자 UUID
        skip: 건너뛸 레코드 수(페이지네이션)
        limit: 반환할 최대 레코드 수
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        페이지네이션이 포함된 다이제스트 목록

    Raises:
        HTTPException: 권한이 없는 경우
    """
    # 권한 확인
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access these digests",
        )

    digests, total = get_user_digests(db, user_id, skip=skip, limit=limit)

    digest_responses = [
        DigestResponse(
            id=digest.id,
            user_id=digest.user_id,
            article_ids=digest.article_ids,
            sent_at=digest.sent_at,
            email_opened=digest.email_opened,
            opened_at=digest.opened_at,
        )
        for digest in digests
    ]

    return DigestListResponse(
        digests=digest_responses,
        total=total,
    )


@router.post("/{user_id}/digests/test")
async def send_test_digest(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    사용자에게 테스트 다이제스트 이메일을 전송한다.

    이 엔드포인트는 사용자 선호도를 기준으로 최근 아티클로 테스트 메일을 보낸다.
    이메일 발송 검증 및 다이제스트 형식 미리보기에 उपयोग한다.

    Args:
        user_id: 사용자 UUID
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        dict: 다이제스트 상세가 포함된 성공 메시지

    Raises:
        HTTPException: 권한이 없거나 선호도를 찾지 못했거나 아티클이 없는 경우
    """
    # 권한 확인
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to send test digest for this user",
        )

    # 사용자 선호도 조회
    preferences = get_user_preference(db, user_id)
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User preferences not found. Please complete onboarding first.",
        )

    # 최근 7일 아티클 조회
    try:
        seven_days_ago = datetime.now() - timedelta(days=7)
        stmt = (
            select(CollectedArticle)
            .where(CollectedArticle.collected_at >= seven_days_ago)
            .order_by(CollectedArticle.importance_score.desc())
            .limit(50)
        )
        result = db.execute(stmt)
        all_articles = list(result.scalars().all())

        if not all_articles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No articles available for digest. Please collect articles first.",
            )

        # 사용자 선호도 기반으로 아티클 선택
        selected_articles = await select_articles_for_user_async(
            articles=all_articles,
            preferences=preferences,
            limit=preferences.daily_limit or 5,
        )

        if not selected_articles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "No articles match your preferences. Try adjusting your keywords or research fields."
                ),
            )

        # 이메일 콘텐츠 생성
        from app.email.builder import EmailBuilder
        from app.email.sender import EmailSender

        builder = EmailBuilder()
        html_content = builder.build_daily_digest(
            user_name=current_user.name,
            user_email=current_user.email,
            articles=selected_articles,
            daily_limit=preferences.daily_limit or 5,
        )

        # 제목 생성
        date_str = datetime.now().strftime("%Y년 %m월 %d일")
        subject = f"🔬 [테스트] Research Curator - {date_str} AI 연구 동향"

        # 이메일 전송
        sender = EmailSender()
        await sender.send_email(
            to_email=current_user.email,
            subject=subject,
            html_content=html_content,
        )

        logger.info(f"Test digest sent successfully to user {user_id}")

        return {
            "message": "Test digest sent successfully",
            "user_id": str(user_id),
            "user_email": current_user.email,
            "article_count": len(selected_articles),
            "total_available": len(all_articles),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending test digest to user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test digest: {str(e)}",
        ) from e
