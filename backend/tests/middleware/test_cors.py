from fastapi import FastAPI

from app.middleware.cors import setup_cors


def test_setup_cors_uses_configured_origins(monkeypatch):
    from app.config.settings import settings

    monkeypatch.setattr(
        settings.security, "cors_origins", ["https://app.example.com"],
    )

    app = FastAPI()
    setup_cors(app)

    cors_middleware = next(
        m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"
    )

    assert cors_middleware.kwargs["allow_origins"] == ["https://app.example.com"]


def test_setup_cors_defaults_to_local_dev_origins():
    from app.config.settings import settings

    app = FastAPI()
    setup_cors(app)

    cors_middleware = next(
        m for m in app.user_middleware if m.cls.__name__ == "CORSMiddleware"
    )

    assert cors_middleware.kwargs["allow_origins"] == settings.security.cors_origins
