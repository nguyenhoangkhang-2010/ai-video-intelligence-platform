from jose import JWTError
from fastapi import Depends
from fastapi import Query

from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials

from sqlalchemy.orm import Session

from app.auth.jwt import decode_token
from app.auth.oauth2 import oauth2_scheme
from app.database.session import get_db

from app.core.exceptions import InactiveUserError

from app.repositories.user import UserRepository

from app.models.user import User


def _load_active_user(
    user_id: int,
    db: Session,
) -> User:
    """
    Shared by every token-verification path below: look up the user
    and enforce is_active. A still-valid token for a since-deactivated
    account must stop working immediately, not just at next login.
    """
    repository = UserRepository(db)

    user = repository.get_by_id(
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    if not user.is_active:
        raise InactiveUserError(
            "This account has been deactivated.",
        )

    return user


def _resolve_user_from_token(
    token: str,
    db: Session,
) -> User:
    try:
        payload = decode_token(token)

        # A media token (see create_media_token) must never be
        # accepted here - this path is for the main, general-purpose
        # access token only. Rejecting it explicitly rather than
        # silently ignoring the scope claim: a media token is scoped
        # to one video and must never grant general API access.
        if payload.get("scope") == "media":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        user_id = int(user_id)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return _load_active_user(user_id, db)


def _resolve_media_token(
    token: str,
    video_id: int,
    db: Session,
) -> User:
    """
    Verify a short-lived media token (see create_media_token) and
    enforce that it was issued for exactly this video_id - a media
    token leaked/logged for one video can never be replayed against
    another. Expiry is enforced by jwt.decode itself (raises
    JWTError past `exp`, same as the main access token).
    """
    try:
        payload = decode_token(token)

        if payload.get("scope") != "media":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        if payload.get("video_id") != video_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Token is not valid for this resource",
            )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        user_id = int(user_id)

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    return _load_active_user(user_id, db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        oauth2_scheme
    ),
    db: Session = Depends(
        get_db,
    )
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    return _resolve_user_from_token(
        credentials.credentials,
        db,
    )


def get_current_user_for_media(
    video_id: int,
    token: str | None = Query(
        default=None,
        description=(
            "Short-lived media token from GET /videos/{video_id}/"
            "media-token, as an alternative to the Authorization "
            "header - needed because browser <video>/<img> elements "
            "cannot attach custom headers. The main long-lived access "
            "token is never accepted here, only a scoped media token "
            "issued for this exact video_id. Reserved for binary "
            "media-delivery endpoints, never JSON API routes."
        ),
    ),
    credentials: HTTPAuthorizationCredentials | None = Depends(
        oauth2_scheme
    ),
    db: Session = Depends(
        get_db,
    ),
) -> User:
    """
    `video_id` is the same path parameter the route itself declares -
    FastAPI resolves it into this dependency automatically, which is
    what lets the query-token path below verify the token was issued
    for *this* resource, not merely *some* video the caller owns.

    The Authorization header path is unchanged (a normal, full-scope
    access token, exactly like get_current_user) - only the query-
    parameter fallback changed: it now requires the dedicated,
    resource-scoped media token (create_media_token) instead of
    accepting the same long-lived token a URL would then expose.
    """
    if credentials is not None:
        return _resolve_user_from_token(
            credentials.credentials,
            db,
        )

    if token is not None:
        return _resolve_media_token(
            token,
            video_id,
            db,
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )