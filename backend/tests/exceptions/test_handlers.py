from fastapi import FastAPI
from fastapi.testclient import TestClient

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
