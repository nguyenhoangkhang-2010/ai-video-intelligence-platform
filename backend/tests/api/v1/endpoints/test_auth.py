import pytest
from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import app


@pytest.fixture
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _register(client, username="alice", email="alice@example.com", password="correct-horse"):
    return client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": password},
    )


# ---- register ----

def test_register_returns_the_created_user_without_the_password(client):
    response = _register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert body["is_active"] is True
    assert "password" not in body
    assert "hashed_password" not in body


def test_register_rejects_duplicate_email_with_409(client):
    _register(client, username="alice", email="dup@example.com")

    response = _register(client, username="someone-else", email="dup@example.com")

    assert response.status_code == 409


def test_register_rejects_duplicate_username_with_409(client):
    _register(client, username="dupname", email="first@example.com")

    response = _register(client, username="dupname", email="second@example.com")

    assert response.status_code == 409


def test_register_rejects_malformed_email_with_422(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "bob", "email": "not-an-email", "password": "whatever"},
    )

    assert response.status_code == 422


# ---- login ----

def test_login_returns_a_real_bearer_token(client):
    _register(client, email="bob@example.com", password="s3cret-pass")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "bob@example.com", "password": "s3cret-pass"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"] != ""


def test_login_rejects_wrong_password_with_401(client):
    _register(client, email="carol@example.com", password="the-real-password")

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "carol@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_login_rejects_unknown_email_with_401(client):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@example.com", "password": "whatever"},
    )

    assert response.status_code == 401


def test_login_rejects_deactivated_account_with_403(client, db_session):
    _register(client, email="dave@example.com", password="dave-password")

    from app.repositories.user import UserRepository

    user = UserRepository(db_session).get_by_email("dave@example.com")
    user.is_active = False
    db_session.commit()

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "dave@example.com", "password": "dave-password"},
    )

    assert response.status_code == 403
