"""Users router for user management and preferences."""

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
)
from app.db.crud.digests import get_user_digests
from app.db.crud.preferences import get_user_preference, update_user_preference
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
    Get current authenticated user information.

    Args:
        current_user: Current user from JWT token

    Returns:
        User information
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
    )


@router.get("/{user_id}/preferences", response_model=UserPreferenceResponse)
def get_preferences(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserPreferenceResponse:
    """
    Get user preferences.

    Args:
        user_id: User UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        User preferences

    Raises:
        HTTPException: If user not authorized or preferences not found
    """
    # Check authorization (users can only access their own preferences)
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

    # Ensure sources is a list (handle legacy dict format)
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
    Update user preferences.

    Args:
        user_id: User UUID
        update_data: Preference update data
        db: Database session
        current_user: Current authenticated user

    Returns:
        Updated user preferences

    Raises:
        HTTPException: If user not authorized or update fails
    """
    # Check authorization
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update these preferences",
        )

    # Update preferences
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
    Get user's digest history.

    Args:
        user_id: User UUID
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of digests with pagination

    Raises:
        HTTPException: If user not authorized
    """
    # Check authorization
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
    Send test digest email to user.

    This endpoint sends a test email with recent articles based on user preferences.
    It's useful for testing the email delivery and previewing the digest format.

    Args:
        user_id: User UUID
        db: Database session
        current_user: Current authenticated user

    Returns:
        dict: Success message with digest details

    Raises:
        HTTPException: If user not authorized, preferences not found, or no articles available
    """
    # Check authorization
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to send test digest for this user",
        )

    # Get user preferences
    preferences = get_user_preference(db, user_id)
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User preferences not found. Please complete onboarding first.",
        )

    # Get recent articles (last 7 days)
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

        # Select articles based on user preferences
        selected_articles = await select_articles_for_user_async(
            articles=all_articles,
            preferences=preferences,
            limit=preferences.daily_limit or 5,
        )

        if not selected_articles:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    "No articles match your preferences. "
                    "Try adjusting your keywords or research fields."
                ),
            )

        # Build email content
        from app.email.builder import EmailBuilder
        from app.email.sender import EmailSender

        builder = EmailBuilder()
        html_content = builder.build_daily_digest(
            user_name=current_user.name,
            user_email=current_user.email,
            articles=selected_articles,
            daily_limit=preferences.daily_limit or 5,
        )

        # Generate subject
        date_str = datetime.now().strftime("%Y년 %m월 %d일")
        subject = f"🔬 [테스트] Research Curator - {date_str} AI 연구 동향"

        # Send email
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
