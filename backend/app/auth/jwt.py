from datetime import datetime
from datetime import timedelta
from datetime import timezone

from jose import jwt

from app.config.settings import settings


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
        algorithm=settings.security.algorithm,
    )

def decode_token(
    token: str,
):
    """Decode JWT token."""

    return jwt.decode(
        token,
        settings.security.secret_key,
        algorithms=[settings.security.algorithm],
    )


def create_media_token(
    user_id: int,
    video_id: int,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Create a short-lived, resource-scoped token for media delivery
    endpoints (video streaming, thumbnails) - never the main access
    token returned by create_access_token.

    Carries `scope="media"` and `video_id` in addition to the usual
    `sub`/`exp` claims, so app.auth.dependencies.get_current_user_for_media
    can both recognize it as a media token (not accept it anywhere a
    normal access token is expected) and reject it outright if
    presented for a different video_id than the one it was issued
    for - a leaked media URL for video A can never be replayed
    against video B.

    Signed with the same secret_key/algorithm as create_access_token
    (no new crypto infrastructure) - only the claims and the default
    expiry differ.
    """
    if expires_delta is None:
        expires_delta = timedelta(
            seconds=settings.security.media_token_expire_seconds,
        )

    expire = datetime.now(
        timezone.utc,
    ) + expires_delta

    payload = {
        "sub": str(user_id),
        "video_id": video_id,
        "scope": "media",
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.security.secret_key,
        algorithm=settings.security.algorithm,
    )