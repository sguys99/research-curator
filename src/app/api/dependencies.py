"""인증 및 DB 접근을 위한 FastAPI 의존성."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import verify_token
from app.db.crud.users import get_user_by_email
from app.db.models import User
from app.db.session import get_db

# HTTP Bearer 토큰 스킴
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    JWT 토큰으로 현재 인증된 사용자를 조회한다.

    Args:
        credentials: HTTP Bearer 인증 정보
        db: 데이터베이스 세션

    Returns:
        User: 현재 사용자 객체

    Raises:
        HTTPException: 토큰이 유효하지 않거나 사용자를 찾지 못한 경우
    """
    token = credentials.credentials

    # 토큰 검증 및 이메일 추출
    email = verify_token(token, expected_type="access")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # DB에서 사용자 조회
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user
