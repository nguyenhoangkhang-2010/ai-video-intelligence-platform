from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.security_headers import setup_security_headers_middleware


def _make_app():
    app = FastAPI()
    setup_security_headers_middleware(app)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    return app


def test_sets_baseline_security_headers_on_every_response():
    client = TestClient(_make_app())

    response = client.get("/ping")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "camera=()" in response.headers["Permissions-Policy"]


def test_headers_present_even_on_a_json_body_unaffected():
    client = TestClient(_make_app())

    response = client.get("/ping")

    # The headers must not interfere with the actual response body.
    assert response.json() == {"ok": True}
    assert response.status_code == 200


def test_no_content_security_policy_header_is_set():
    """
    Deliberately not set on this backend (see the middleware's
    docstring) - a JSON API/video-stream process has no rendered HTML
    for real users to protect with CSP, and setting one blindly here
    risks breaking /docs or /redoc without the dedicated testing a real
    CSP needs.
    """
    client = TestClient(_make_app())

    response = client.get("/ping")

    assert "Content-Security-Policy" not in response.headers
