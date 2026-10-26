import pytest

from app.core.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from app.core.security import verify_password
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserLogin
from app.services.auth_service import AuthService


@pytest.fixture
def auth_service(db_session):
    return AuthService(UserRepository(db_session))


def _register(auth_service, username="alice", email="alice@example.com", password="correct-horse"):
    return auth_service.register(
        UserCreate(username=username, email=email, password=password),
    )


# ---- register ----

def test_register_creates_a_user_with_a_hashed_password(auth_service):
    user = _register(auth_service)

    assert user.id is not None
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    # The plaintext password is never stored - only a hash that the
    # real verify_password round-trip accepts.
    assert user.hashed_password != "correct-horse"
    assert verify_password("correct-horse", user.hashed_password)


def test_register_rejects_duplicate_email(auth_service):
    _register(auth_service, username="alice", email="dup@example.com")

    with pytest.raises(UserAlreadyExistsError):
        _register(auth_service, username="someone-else", email="dup@example.com")


def test_register_rejects_duplicate_username(auth_service):
    _register(auth_service, username="dupname", email="first@example.com")

    with pytest.raises(UserAlreadyExistsError):
        _register(auth_service, username="dupname", email="second@example.com")


# ---- login ----

def test_login_returns_a_token_for_correct_credentials(auth_service):
    _register(auth_service, email="bob@example.com", password="s3cret-pass")

    token = auth_service.login(
        UserLogin(email="bob@example.com", password="s3cret-pass"),
    )

    assert isinstance(token, str)
    assert token != ""


def test_login_rejects_unknown_email(auth_service):
    with pytest.raises(InvalidCredentialsError):
        auth_service.login(
            UserLogin(email="nobody@example.com", password="whatever"),
        )


def test_login_rejects_wrong_password(auth_service):
    _register(auth_service, email="carol@example.com", password="the-real-password")

    with pytest.raises(InvalidCredentialsError):
        auth_service.login(
            UserLogin(email="carol@example.com", password="wrong-password"),
        )


def test_login_rejects_deactivated_account_with_correct_password(auth_service, db_session):
    user = _register(auth_service, email="dave@example.com", password="dave-password")
    user.is_active = False
    db_session.commit()

    with pytest.raises(InactiveUserError):
        auth_service.login(
            UserLogin(email="dave@example.com", password="dave-password"),
        )


def test_login_still_rejects_wrong_password_for_deactivated_account_as_invalid_credentials(
    auth_service, db_session,
):
    """
    Credentials are checked before is_active, so a deactivated
    account with a WRONG password still reports "invalid credentials"
    (401), not "deactivated" (403) - an attacker who doesn't know the
    real password can't use the error to learn the account is
    disabled.
    """
    user = _register(auth_service, email="erin@example.com", password="erin-password")
    user.is_active = False
    db_session.commit()

    with pytest.raises(InvalidCredentialsError):
        auth_service.login(
            UserLogin(email="erin@example.com", password="not-the-password"),
        )
