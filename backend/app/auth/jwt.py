from datetime import datetime
from datetime import timedelta
from datetime import timezone

from jose import jwt

from app.config.settings import settings


ALGORITHM = "HS256"


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token."""

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.security.access_token_expire_minutes,
        )

    expire = datetime.now(
        timezone.utc,
    ) + expires_delta

    payload = {
        "sub": subject,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.security.secret_key,
        algorithm=ALGORITHM,
    )
    
def decode_token(
    token: str,
):
    """Decode JWT token."""

    return jwt.decode(
        token,
        settings.security.secret_key,
        algorithms=[ALGORITHM],
    )