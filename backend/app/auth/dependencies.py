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


def _resolve_user_from_token(
    token: str,
    db: Session,
) -> User:
    try:
        payload = decode_token(token)

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
        # A still-valid token for a since-deactivated account must
        # stop working immediately, not just at next login - checked
        # here since every protected endpoint (get_current_user and
        # get_current_user_for_media) funnels through this function.
        raise InactiveUserError(
            "This account has been deactivated.",
        )

    return user


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
    token: str | None = Query(
        default=None,
        description=(
            "JWT access token, as an alternative to the Authorization "
            "header - needed because browser <video>/<img> elements "
            "cannot attach custom headers. Only accepted on "
            "media-delivery endpoints, never on JSON API routes."
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
    Same authentication as get_current_user (identical JWT
    validation/user lookup), but also accepts the token via a `token`
    query parameter as a fallback when no Authorization header is
    present. Reserved for binary media-delivery endpoints (e.g. video
    streaming) where the client is a native <video> element rather
    than an API call the frontend controls headers for.
    """
    if credentials is not None:
        return _resolve_user_from_token(
            credentials.credentials,
            db,
        )

    if token is not None:
        return _resolve_user_from_token(
            token,
            db,
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )