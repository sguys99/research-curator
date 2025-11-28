"""Security utilities for authentication and authorization."""

from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from app.core.config import settings


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
        email: str = payload.get("sub")
        token_type: str = payload.get("type")

        if email is None or token_type != expected_type:
            return None

        return email
    except JWTError:
        return None
