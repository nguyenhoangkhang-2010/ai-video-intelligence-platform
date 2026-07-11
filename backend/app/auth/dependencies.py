from jose import JWTError
from fastapi import Depends

from fastapi import HTTPException
from fastapi import status

from sqlalchemy.orm import Session

from app.auth.jwt import decode_token
from app.auth.oauth2 import oauth2_scheme
from app.database.session import get_db

from app.repositories.user import UserRepository


def get_current_user(
    token: str = Depends(
        oauth2_scheme,
    ),
    db: Session = Depends(
        get_db,
    )
):
    try:
        payload = decode_token(token)

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    repository = UserRepository(db)

    user = repository.get_by_id(
        int(user_id),
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user