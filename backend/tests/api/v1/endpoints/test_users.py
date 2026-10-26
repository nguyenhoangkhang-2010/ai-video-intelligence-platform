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


def test_me_requires_authentication(client):
    response = client.get("/api/v1/users/me")

    assert response.status_code == 401


def test_me_rejects_a_malformed_token(client):
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 401


def test_me_returns_the_authenticated_user_via_a_real_jwt_round_trip(client):
    """
    End-to-end through the real auth chain, not a mocked
    get_current_user override: register -> login -> use the real
    issued token -> /me resolves it back to the same user. No
    password/hash in the response.
    """
    client.post(
        "/api/v1/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "correct-horse"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "correct-horse"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert "password" not in body
    assert "hashed_password" not in body
