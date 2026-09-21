from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError

from app.auth.dependencies import get_current_user, get_current_user_for_media


def _credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _make_user(user_id: int):
    user = MagicMock(name="user")
    user.id = user_id
    return user


# ---- get_current_user ----

def test_get_current_user_raises_401_when_no_credentials_provided():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=None, db=MagicMock())

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"


def test_get_current_user_returns_user_for_valid_token():
    db = MagicMock()

    with (
        patch("app.auth.dependencies.decode_token", return_value={"sub": "42"}),
        patch("app.auth.dependencies.UserRepository") as mock_repo_cls,
    ):
        mock_repo_cls.return_value.get_by_id.return_value = _make_user(42)

        user = get_current_user(credentials=_credentials("valid-token"), db=db)

    assert user.id == 42


def test_get_current_user_raises_401_for_invalid_token():
    with patch("app.auth.dependencies.decode_token", side_effect=JWTError("bad token")):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=_credentials("bad-token"), db=MagicMock())

    assert exc_info.value.status_code == 401


def test_get_current_user_raises_401_when_user_no_longer_exists():
    with (
        patch("app.auth.dependencies.decode_token", return_value={"sub": "42"}),
        patch("app.auth.dependencies.UserRepository") as mock_repo_cls,
    ):
        mock_repo_cls.return_value.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(credentials=_credentials("valid-token"), db=MagicMock())

    assert exc_info.value.status_code == 401


# ---- get_current_user_for_media ----

def test_get_current_user_for_media_prefers_authorization_header():
    with (
        patch("app.auth.dependencies.decode_token", return_value={"sub": "7"}),
        patch("app.auth.dependencies.UserRepository") as mock_repo_cls,
    ):
        mock_repo_cls.return_value.get_by_id.return_value = _make_user(7)

        user = get_current_user_for_media(
            token="ignored-when-header-present",
            credentials=_credentials("header-token"),
            db=MagicMock(),
        )

    assert user.id == 7


def test_get_current_user_for_media_falls_back_to_query_token():
    with (
        patch("app.auth.dependencies.decode_token", return_value={"sub": "7"}),
        patch("app.auth.dependencies.UserRepository") as mock_repo_cls,
    ):
        mock_repo_cls.return_value.get_by_id.return_value = _make_user(7)

        user = get_current_user_for_media(
            token="query-token",
            credentials=None,
            db=MagicMock(),
        )

    assert user.id == 7


def test_get_current_user_for_media_raises_401_when_neither_provided():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user_for_media(token=None, credentials=None, db=MagicMock())

    assert exc_info.value.status_code == 401
