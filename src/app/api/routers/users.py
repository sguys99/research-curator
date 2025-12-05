"""Users router for user management and preferences."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
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
from app.db.models import User
from app.db.session import get_db

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
