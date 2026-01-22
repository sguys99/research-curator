"""사용자 피드백 관리를 위한 라우터."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.api.schemas.feedback import (
    FeedbackCreate,
    FeedbackListResponse,
    FeedbackResponse,
    FeedbackStatsResponse,
    FeedbackUpdate,
)
from app.db.crud.articles import get_article_by_id
from app.db.crud.feedback import (
    create_feedback,
    delete_feedback,
    get_article_feedback,
    get_article_feedback_stats,
    get_feedback_by_id,
    get_user_feedback,
    update_feedback,
)
from app.db.models import User
from app.db.session import get_db

router = APIRouter(tags=["feedback"], prefix="/feedback")


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def create_user_feedback(
    feedback_data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackResponse:
    """
    아티클에 대한 새 피드백을 생성한다.

    Args:
        feedback_data: 피드백 생성 데이터
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        생성된 피드백

    Raises:
        HTTPException: 아티클을 찾지 못했거나 검증 실패 시
    """
    # 아티클 존재 여부 확인
    article = get_article_by_id(db, feedback_data.article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    # 피드백 생성
    feedback = create_feedback(
        db,
        user_id=current_user.id,
        article_id=feedback_data.article_id,
        rating=feedback_data.rating,
        comment=feedback_data.comment,
    )

    return FeedbackResponse(
        id=feedback.id,
        user_id=feedback.user_id,
        article_id=feedback.article_id,
        rating=feedback.rating,
        comment=feedback.comment,
        created_at=feedback.created_at,
    )


@router.get("/{feedback_id}", response_model=FeedbackResponse)
def get_feedback(
    feedback_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackResponse:
    """
    ID로 단일 피드백을 조회한다.

    Args:
        feedback_id: 피드백 UUID
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        피드백 상세 정보

    Raises:
        HTTPException: 피드백을 찾지 못했거나 권한이 없는 경우
    """
    feedback = get_feedback_by_id(db, feedback_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    # 권한 확인(사용자는 자신의 피드백만 조회 가능)
    if str(feedback.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this feedback",
        )

    return FeedbackResponse(
        id=feedback.id,
        user_id=feedback.user_id,
        article_id=feedback.article_id,
        rating=feedback.rating,
        comment=feedback.comment,
        created_at=feedback.created_at,
    )


@router.put("/{feedback_id}", response_model=FeedbackResponse)
def update_user_feedback(
    feedback_id: UUID,
    feedback_data: FeedbackUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackResponse:
    """
    피드백을 수정한다.

    Args:
        feedback_id: 피드백 UUID
        feedback_data: 피드백 수정 데이터
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        수정된 피드백

    Raises:
        HTTPException: 피드백을 찾지 못했거나 권한이 없는 경우
    """
    # 피드백 존재 여부 확인
    existing_feedback = get_feedback_by_id(db, feedback_id)
    if not existing_feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    # 권한 확인
    if str(existing_feedback.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this feedback",
        )

    # 피드백 수정
    updated_feedback = update_feedback(
        db,
        feedback_id,
        rating=feedback_data.rating,
        comment=feedback_data.comment,
    )

    if not updated_feedback:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feedback",
        )

    return FeedbackResponse(
        id=updated_feedback.id,
        user_id=updated_feedback.user_id,
        article_id=updated_feedback.article_id,
        rating=updated_feedback.rating,
        comment=updated_feedback.comment,
        created_at=updated_feedback.created_at,
    )


@router.delete("/{feedback_id}")
def delete_user_feedback(
    feedback_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """
    피드백을 삭제한다.

    Args:
        feedback_id: 피드백 UUID
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        성공 메시지

    Raises:
        HTTPException: 피드백을 찾지 못했거나 권한이 없는 경우
    """
    # 피드백 존재 여부 확인
    existing_feedback = get_feedback_by_id(db, feedback_id)
    if not existing_feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    # 권한 확인
    if str(existing_feedback.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this feedback",
        )

    # 피드백 삭제
    success = delete_feedback(db, feedback_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete feedback",
        )

    return {"message": "Feedback deleted successfully"}


@router.get("/user/{user_id}", response_model=FeedbackListResponse)
def get_user_feedback_list(
    user_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackListResponse:
    """
    사용자의 피드백 목록을 조회한다.

    Args:
        user_id: 사용자 UUID
        skip: 건너뛸 레코드 수
        limit: 반환할 최대 레코드 수
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        사용자 피드백 목록

    Raises:
        HTTPException: 권한이 없는 경우
    """
    # 권한 확인(사용자는 자신의 피드백만 조회 가능)
    if str(user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this user's feedback",
        )

    feedback_list, total = get_user_feedback(db, user_id, skip=skip, limit=limit)

    feedback_responses = [
        FeedbackResponse(
            id=feedback.id,
            user_id=feedback.user_id,
            article_id=feedback.article_id,
            rating=feedback.rating,
            comment=feedback.comment,
            created_at=feedback.created_at,
        )
        for feedback in feedback_list
    ]

    return FeedbackListResponse(
        feedback=feedback_responses,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/article/{article_id}", response_model=FeedbackListResponse)
def get_article_feedback_list(
    article_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackListResponse:
    """
    특정 아티클의 피드백 목록을 조회한다.

    Args:
        article_id: 아티클 UUID
        skip: 건너뛸 레코드 수
        limit: 반환할 최대 레코드 수
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        아티클 피드백 목록
    """
    # 아티클 존재 여부 확인
    article = get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    feedback_list, total = get_article_feedback(db, article_id, skip=skip, limit=limit)

    feedback_responses = [
        FeedbackResponse(
            id=feedback.id,
            user_id=feedback.user_id,
            article_id=feedback.article_id,
            rating=feedback.rating,
            comment=feedback.comment,
            created_at=feedback.created_at,
        )
        for feedback in feedback_list
    ]

    return FeedbackListResponse(
        feedback=feedback_responses,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/article/{article_id}/stats", response_model=FeedbackStatsResponse)
def get_article_stats(
    article_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FeedbackStatsResponse:
    """
    특정 아티클의 피드백 통계를 조회한다.

    Args:
        article_id: 아티클 UUID
        db: 데이터베이스 세션
        current_user: 현재 인증된 사용자

    Returns:
        피드백 통계(count, average_rating, rating_distribution)

    Raises:
        HTTPException: 아티클을 찾지 못한 경우
    """
    # 아티클 존재 여부 확인
    article = get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    stats = get_article_feedback_stats(db, article_id)

    return FeedbackStatsResponse(
        article_id=article_id,
        count=stats["count"],
        average_rating=stats["average_rating"],
        rating_distribution=stats["rating_distribution"],
    )
