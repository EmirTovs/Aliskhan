
from datetime import datetime, timedelta, timezone
from uuid import UUID

from jose import JWTError, jwt
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Создаёт безопасный хеш пароля."""
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Проверяет пароль по сохранённому хешу."""
    return password_hash.verify(password, hashed_password)


def create_access_token(user_id: UUID) -> str:
    """Создаёт JWT-токен пользователя."""
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> UUID | None:
    """Проверяет JWT и возвращает ID пользователя."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        subject = payload.get("sub")

        if not subject:
            return None

        return UUID(subject)

    except (JWTError, ValueError, TypeError):
        return None
