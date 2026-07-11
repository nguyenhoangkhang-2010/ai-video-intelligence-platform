from datetime import datetime
from datetime import timedelta
from datetime import timezone

from jose import jwt

from app.config import settings


ALGORITHM = "HS256"


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token."""

    if expires_delta is None:
        expires_delta = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
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
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )
    
def decode_token(
    token: str,
):
    """Decode JWT token."""

    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[ALGORITHM],
    )