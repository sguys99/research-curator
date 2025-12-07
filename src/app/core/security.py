"""Security utilities for authentication and authorization."""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.core.config import settings


# 매직링크 인증 플로우
# 1. 사용자가 이메일 입력
#    ↓
# 2. 서버가 매직 링크 토큰 생성 (create_magic_link_token)
#    ↓
# 3. 이메일로 링크 전송
#    예: https://app.com/verify?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
#    ↓
# 4. 사용자가 링크 클릭
#    ↓
# 5. 서버가 토큰 검증 (verify_token)
#    ↓
# 6. 토큰이 유효하면 로그인 완료 + 세션 토큰 발급 (create_access_token)
def create_magic_link_token(email: str) -> str:
    """
    Create a JWT token for magic link authentication.

    Args:
        email: User email address

    Returns:
        JWT token string
    """
    expire = datetime.now(UTC) + timedelta(minutes=settings.MAGIC_LINK_EXPIRE_MINUTES)
    payload = {
        "sub": email,
        "exp": expire,
        "type": "magic_link",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# 용도, 수명 주기가 달라서 위와 구분함, 단일 책임 원칙(SRP)를 따라 구분
def create_access_token(email: str) -> str:
    """
    Create a JWT access token for authenticated sessions.

    Args:
        email: User email address

    Returns:
        JWT token string
    """
    expire = datetime.now(UTC) + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": email,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


# 토큰을 검증하여, 사용자 식별을 위해 이메일을 리턴
def verify_token(token: str, expected_type: str = "access") -> str | None:
    """
    Verify JWT token and return email if valid.

    Args:
        token: JWT token to verify
        expected_type: Expected token type (magic_link or access)

    Returns:
        Email if token is valid, None otherwise
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        # payload.get()은 Any | None을 반환하므로 타입 명시 제거
        email = payload.get("sub")
        token_type = payload.get("type")

        # None 체크 및 타입 검증
        if email is None or token_type != expected_type:
            return None

        return email
    except JWTError:
        return None
