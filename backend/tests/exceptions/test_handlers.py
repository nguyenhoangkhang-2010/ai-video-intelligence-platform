from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    VideoNotFoundError,
)
from app.exceptions.handlers import setup_exception_handlers


def _make_app():
    app = FastAPI()
    setup_exception_handlers(app)

    @app.get("/boom")
    def boom():
        raise RuntimeError("something internal broke with a secret path /etc/passwd")

    @app.get("/ok")
    def ok():
        return {"status": "ok"}

    @app.get("/invalid-credentials")
    def invalid_credentials():
        raise InvalidCredentialsError("Invalid email or password.")

    @app.get("/already-exists")
    def already_exists():
        raise UserAlreadyExistsError("Email already exists.")

    @app.get("/video-not-found")
    def video_not_found():
        raise VideoNotFoundError("Video not found.")

    return app


def test_unhandled_exception_returns_generic_500_json():
    app = _make_app()

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}


def test_unhandled_exception_does_not_leak_internal_details():
    app = _make_app()

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/boom")

    body_text = response.text
    assert "RuntimeError" not in body_text
    assert "/etc/passwd" not in body_text
    assert "Traceback" not in body_text


def test_normal_requests_are_unaffected_by_the_handler():
    app = _make_app()

    with TestClient(app) as client:
        response = client.get("/ok")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invalid_credentials_error_maps_to_401():
    app = _make_app()

    with TestClient(app) as client:
        response = client.get("/invalid-credentials")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password."}


def test_user_already_exists_error_maps_to_409():
    app = _make_app()

    with TestClient(app) as client:
        response = client.get("/already-exists")

    assert response.status_code == 409
    assert response.json() == {"detail": "Email already exists."}


def test_video_not_found_error_maps_to_404():
    app = _make_app()

    with TestClient(app) as client:
        response = client.get("/video-not-found")

    assert response.status_code == 404
    assert response.json() == {"detail": "Video not found."}
