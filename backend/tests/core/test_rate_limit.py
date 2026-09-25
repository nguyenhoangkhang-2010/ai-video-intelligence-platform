from unittest.mock import MagicMock, patch

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.rate_limit import rate_limit


def _make_app(category="test", limit=3, window=60):
    app = FastAPI()

    @app.get("/ping", dependencies=[Depends(rate_limit(category, limit, window))])
    def ping():
        return {"ok": True}

    return app


@pytest.fixture(autouse=True)
def _reset_module_state():
    # rate_limit.py caches a client/init-failure flag at module scope -
    # each test gets a clean slate so one test's Redis mock doesn't leak
    # into the next.
    import app.core.rate_limit as rl

    rl._client = None
    rl._client_init_failed = False
    rl._unavailable_logged = False
    yield
    rl._client = None
    rl._client_init_failed = False
    rl._unavailable_logged = False


def test_allows_requests_under_the_limit():
    fake_redis = MagicMock()
    fake_redis.incr.side_effect = [1, 2, 3]

    with patch("app.core.rate_limit._get_client", return_value=fake_redis), \
         patch("app.core.rate_limit.settings.rate_limit.enabled", True):
        client = TestClient(_make_app(limit=3))
        for _ in range(3):
            response = client.get("/ping")
            assert response.status_code == 200


def test_blocks_with_429_once_limit_is_exceeded():
    fake_redis = MagicMock()
    fake_redis.incr.side_effect = [1, 2, 3, 4]

    with patch("app.core.rate_limit._get_client", return_value=fake_redis), \
         patch("app.core.rate_limit.settings.rate_limit.enabled", True):
        client = TestClient(_make_app(limit=3))
        for _ in range(3):
            assert client.get("/ping").status_code == 200
        response = client.get("/ping")
        assert response.status_code == 429


def test_sets_expiry_only_on_the_first_request_in_a_window():
    fake_redis = MagicMock()
    fake_redis.incr.side_effect = [1, 2]

    with patch("app.core.rate_limit._get_client", return_value=fake_redis), \
         patch("app.core.rate_limit.settings.rate_limit.enabled", True):
        client = TestClient(_make_app(limit=5, window=60))
        client.get("/ping")
        client.get("/ping")

    assert fake_redis.expire.call_count == 1


def test_fails_open_when_redis_is_unreachable():
    with patch("app.core.rate_limit._get_client", return_value=None), \
         patch("app.core.rate_limit.settings.rate_limit.enabled", True):
        client = TestClient(_make_app(limit=1))
        # Well over the limit, but Redis is unavailable - must never 429.
        for _ in range(5):
            assert client.get("/ping").status_code == 200


def test_fails_open_when_redis_raises_during_incr():
    fake_redis = MagicMock()
    fake_redis.incr.side_effect = ConnectionError("redis down")

    with patch("app.core.rate_limit._get_client", return_value=fake_redis), \
         patch("app.core.rate_limit.settings.rate_limit.enabled", True):
        client = TestClient(_make_app(limit=1))
        assert client.get("/ping").status_code == 200


def test_disabled_via_settings_never_limits():
    fake_redis = MagicMock()
    fake_redis.incr.return_value = 999

    with patch("app.core.rate_limit._get_client", return_value=fake_redis), \
         patch("app.core.rate_limit.settings.rate_limit.enabled", False):
        client = TestClient(_make_app(limit=1))
        assert client.get("/ping").status_code == 200
        fake_redis.incr.assert_not_called()
