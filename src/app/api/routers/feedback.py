"""Feedback router for user feedback management."""

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
    Create new feedback for an article.

    Args:
        feedback_data: Feedback creation data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Created feedback

    Raises:
        HTTPException: If article not found or validation fails
    """
    # Verify article exists
    from app.db.crud.articles import get_article_by_id

    article = get_article_by_id(db, feedback_data.article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )

    # Create feedback
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
    Get single feedback by ID.

    Args:
        feedback_id: Feedback UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Feedback details

    Raises:
        HTTPException: If feedback not found or not authorized
    """
    feedback = get_feedback_by_id(db, feedback_id)
    if not feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    # Check authorization (users can only view their own feedback)
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
    Update feedback.

    Args:
        feedback_id: Feedback UUID
        feedback_data: Feedback update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated feedback

    Raises:
        HTTPException: If feedback not found or not authorized
    """
    # Check if feedback exists
    existing_feedback = get_feedback_by_id(db, feedback_id)
    if not existing_feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    # Check authorization
    if str(existing_feedback.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this feedback",
        )

    # Update feedback
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
    Delete feedback.

    Args:
        feedback_id: Feedback UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Success message

    Raises:
        HTTPException: If feedback not found or not authorized
    """
    # Check if feedback exists
    existing_feedback = get_feedback_by_id(db, feedback_id)
    if not existing_feedback:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feedback not found",
        )

    # Check authorization
    if str(existing_feedback.user_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this feedback",
        )

    # Delete feedback
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
    Get user's feedback list.

    Args:
        user_id: User UUID
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of user's feedback

    Raises:
        HTTPException: If not authorized
    """
    # Check authorization (users can only view their own feedback)
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
    Get feedback for a specific article.

    Args:
        article_id: Article UUID
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of article's feedback
    """
    # Verify article exists
    from app.db.crud.articles import get_article_by_id

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
    Get feedback statistics for an article.

    Args:
        article_id: Article UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        Feedback statistics (count, average_rating, rating_distribution)

    Raises:
        HTTPException: If article not found
    """
    # Verify article exists
    from app.db.crud.articles import get_article_by_id

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
