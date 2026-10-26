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


# --- Trusted-proxy-aware client IP resolution ----------------------------
#
# Regression coverage for the real gap identified in the security
# audit: in the documented production topology (nginx in front of
# uvicorn, uvicorn started without --proxy-headers), request.client.
# host is nginx's own container IP for every request, collapsing the
# per-IP rate limit into one shared bucket for the entire site. These
# tests exercise _resolve_client_ip directly against a raw Request-
# like object rather than through a full TestClient, since
# TestClient's own synthetic client host is harder to control
# per-request.


def _request(client_host: str, forwarded_for: str | None = None):
    request = MagicMock()
    request.client.host = client_host
    request.headers = {"x-forwarded-for": forwarded_for} if forwarded_for else {}
    return request


def test_resolve_client_ip_uses_direct_peer_when_not_trusted():
    from app.core.rate_limit import _resolve_client_ip

    with patch("app.core.rate_limit.settings.rate_limit.trusted_proxy_ips", []):
        request = _request("203.0.113.9", forwarded_for="198.51.100.1")

        assert _resolve_client_ip(request) == "203.0.113.9"


def test_resolve_client_ip_ignores_forwarded_header_from_an_untrusted_peer():
    """
    Safety-critical: an attacker who is NOT behind a trusted proxy
    must not be able to bypass their own IP's rate limit just by
    sending a fabricated X-Forwarded-For header.
    """
    from app.core.rate_limit import _resolve_client_ip

    with patch("app.core.rate_limit.settings.rate_limit.trusted_proxy_ips", ["10.0.0.5"]):
        request = _request("203.0.113.9", forwarded_for="198.51.100.1")

        assert _resolve_client_ip(request) == "203.0.113.9"


def test_resolve_client_ip_uses_forwarded_header_from_a_trusted_proxy():
    from app.core.rate_limit import _resolve_client_ip

    with patch("app.core.rate_limit.settings.rate_limit.trusted_proxy_ips", ["10.0.0.5"]):
        request = _request("10.0.0.5", forwarded_for="198.51.100.1")

        assert _resolve_client_ip(request) == "198.51.100.1"


def test_resolve_client_ip_takes_the_first_hop_of_a_forwarded_chain():
    from app.core.rate_limit import _resolve_client_ip

    with patch("app.core.rate_limit.settings.rate_limit.trusted_proxy_ips", ["10.0.0.5"]):
        request = _request("10.0.0.5", forwarded_for="198.51.100.1, 10.0.0.5")

        assert _resolve_client_ip(request) == "198.51.100.1"


def test_resolve_client_ip_falls_back_to_direct_peer_when_trusted_but_header_missing():
    from app.core.rate_limit import _resolve_client_ip

    with patch("app.core.rate_limit.settings.rate_limit.trusted_proxy_ips", ["10.0.0.5"]):
        request = _request("10.0.0.5", forwarded_for=None)

        assert _resolve_client_ip(request) == "10.0.0.5"


def test_two_distinct_clients_behind_a_trusted_proxy_get_separate_limits():
    """
    End-to-end through the real rate_limit dependency (not just
    _resolve_client_ip in isolation): once the direct peer is
    trusted, two different X-Forwarded-For clients must be counted
    separately, not pooled into nginx's single container IP.
    """
    fake_redis = MagicMock()
    fake_redis.incr.side_effect = [1, 1]

    app = FastAPI()

    @app.get("/ping", dependencies=[Depends(rate_limit("test", 1, 60))])
    def ping():
        return {"ok": True}

    with patch("app.core.rate_limit._get_client", return_value=fake_redis), \
         patch("app.core.rate_limit.settings.rate_limit.enabled", True), \
         patch("app.core.rate_limit.settings.rate_limit.trusted_proxy_ips", ["testclient"]):
        client = TestClient(app)
        r1 = client.get("/ping", headers={"X-Forwarded-For": "198.51.100.1"})
        r2 = client.get("/ping", headers={"X-Forwarded-For": "198.51.100.2"})

    assert r1.status_code == 200
    assert r2.status_code == 200
    keys_used = {call.args[0] for call in fake_redis.incr.call_args_list}
    assert keys_used == {
        "ratelimit:test:198.51.100.1",
        "ratelimit:test:198.51.100.2",
    }


def test_disabled_via_settings_never_limits():
    fake_redis = MagicMock()
    fake_redis.incr.return_value = 999

    with patch("app.core.rate_limit._get_client", return_value=fake_redis), \
         patch("app.core.rate_limit.settings.rate_limit.enabled", False):
        client = TestClient(_make_app(limit=1))
        assert client.get("/ping").status_code == 200
        fake_redis.incr.assert_not_called()
