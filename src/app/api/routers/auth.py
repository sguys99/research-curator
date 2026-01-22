"""매직 링크 및 JWT 토큰 관리를 위한 인증 라우터."""

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
    비밀번호 없이 인증 가능한 매직 링크를 요청한다.

    운영 환경에서는 이메일로 매직 링크를 전송한다.
    개발 환경에서는 응답에 토큰을 포함해 반환한다.

    Args:
        request: 이메일이 포함된 매직 링크 요청
        db: 데이터베이스 세션

    Returns:
        메시지와 선택적 토큰을 포함한 응답
    """
    # 사용자 조회 또는 생성
    user = get_user_by_email(db, request.email)
    if not user:
        user = create_user(db, email=request.email)

    # 매직 링크 토큰 생성
    token = create_magic_link_token(request.email)

    # 매직 링크 이메일 전송
    try:
        from app.email.builder import EmailBuilder
        from app.email.sender import EmailSender

        # 매직 링크 URL 생성
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:8501")
        magic_link = f"{frontend_url}/?token={token}"

        # EmailBuilder로 이메일 콘텐츠 생성 (네이버 호환 CSS 인라이닝 포함)
        builder = EmailBuilder()
        html_content = builder.build_magic_link_email(magic_link, request.email)

        # 이메일 전송
        sender = EmailSender()
        await sender.send_email(
            to_email=request.email,
            subject="🔬 Research Curator 로그인 링크",
            html_content=html_content,
        )

        # 환경에 따른 응답 반환
        if settings.ENVIRONMENT == "development":
            return MagicLinkResponse(
                message="매직 링크가 이메일로 발송되었습니다!",
                token=token,  # 개발 환경 디버깅을 위해 토큰 반환
            )
        else:
            return MagicLinkResponse(
                message="매직 링크가 이메일로 발송되었습니다. 이메일을 확인해주세요.",
                token=None,
            )

    except Exception as e:
        # 이메일 전송 실패 시에도 개발 모드는 동작하도록 처리
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
    매직 링크 토큰을 검증하고 액세스 토큰을 반환한다.

    Args:
        token: 매직 링크 JWT 토큰
        db: 데이터베이스 세션

    Returns:
        액세스 토큰과 사용자 정보

    Raises:
        HTTPException: 토큰이 유효하지 않거나 만료된 경우
    """
    # 매직 링크 토큰 검증
    email = verify_token(token, expected_type="magic_link")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired magic link token",
        )

    # 사용자 조회
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 마지막 로그인 갱신
    update_user_last_login(db, user.id)

    # 액세스 토큰 생성
    access_token = create_access_token(email)

    # 응답을 위한 사용자 딕셔너리 변환
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
