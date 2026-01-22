"""Authentication router for magic link and JWT token management."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.auth import MagicLinkRequest, MagicLinkResponse, TokenResponse
from app.core.config import settings
from app.core.security import create_access_token, create_magic_link_token, verify_token
from app.db.crud.users import create_user, get_user_by_email, update_user_last_login
from app.db.session import get_db

router = APIRouter(tags=["auth"])


@router.post("/magic-link", response_model=MagicLinkResponse)
async def request_magic_link(
    request: MagicLinkRequest,
    db: Session = Depends(get_db),
) -> MagicLinkResponse:
    """
    Request a magic link for passwordless authentication.

    In production, this would send an email with the magic link.
    In development mode, the token is returned directly in the response.

    Args:
        request: Magic link request with email
        db: Database session

    Returns:
        Magic link response with message and optional token
    """
    # Get or create user
    user = get_user_by_email(db, request.email)
    if not user:
        user = create_user(db, email=request.email)

    # Create magic link token
    token = create_magic_link_token(request.email)

    # Send email with magic link
    try:
        from app.email.builder import EmailBuilder
        from app.email.sender import EmailSender

        # Generate magic link URL
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:8501")
        magic_link = f"{frontend_url}/?token={token}"

        # Build email content using EmailBuilder (with CSS inlining for Naver compatibility)
        builder = EmailBuilder()
        html_content = builder.build_magic_link_email(magic_link, request.email)

        # Send email
        sender = EmailSender()
        await sender.send_email(
            to_email=request.email,
            subject="🔬 Research Curator 로그인 링크",
            html_content=html_content,
        )

        # Return response based on environment
        if settings.ENVIRONMENT == "development":
            return MagicLinkResponse(
                message="매직 링크가 이메일로 발송되었습니다!",
                token=token,  # Show token in development for debugging
            )
        else:
            return MagicLinkResponse(
                message="매직 링크가 이메일로 발송되었습니다. 이메일을 확인해주세요.",
                token=None,
            )

    except Exception as e:
        # If email sending fails, still allow development mode to work
        if settings.ENVIRONMENT == "development":
            return MagicLinkResponse(
                message=f"이메일 발송 실패 (개발 모드 - 토큰 직접 사용 가능): {str(e)}",
                token=token,
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"이메일 발송에 실패했습니다: {str(e)}",
            ) from e


@router.get("/verify", response_model=TokenResponse)
def verify_magic_link(
    token: str,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Verify magic link token and return access token.

    Args:
        token: Magic link JWT token
        db: Database session

    Returns:
        Access token and user information

    Raises:
        HTTPException: If token is invalid or expired
    """
    # Verify magic link token
    email = verify_token(token, expected_type="magic_link")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired magic link token",
        )

    # Get user
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update last login
    update_user_last_login(db, user.id)

    # Create access token
    access_token = create_access_token(email)

    # Convert user to dict for response
    user_data = {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat(),
    }

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_data,
    )
