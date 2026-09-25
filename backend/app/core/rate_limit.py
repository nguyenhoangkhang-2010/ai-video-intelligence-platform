"""
Redis-backed rate limiting for abuse-prone endpoints.

Fixed-window counter via Redis INCR+EXPIRE (atomic per key on Redis's
single-threaded command execution - no read-modify-write race, no need
for a Lua script) - simple and sufficient for abuse protection without
a sliding-window/token-bucket algorithm's added complexity for a
product this size. Keyed by client IP, per category (login/register/
upload/search/export), each with its own env-driven limit (see
app.config.settings.RateLimitSettings).

Fails OPEN (never blocks a request) if Redis is unreachable - product
availability must not depend on the rate limiter's own infrastructure
being healthy. A Redis outage should not also mean nobody can log in.
"""
import logging

import redis
from fastapi import HTTPException, Request, status

from app.config.settings import settings

logger = logging.getLogger("api.rate_limit")

_client: redis.Redis | None = None
_client_init_failed = False
_unavailable_logged = False


def _get_client() -> redis.Redis | None:
    global _client, _client_init_failed
    if _client is not None:
        return _client
    if _client_init_failed:
        return None
    try:
        _client = redis.Redis.from_url(
            settings.rate_limit.redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
    except Exception:
        _client_init_failed = True
        return None
    return _client


def rate_limit(category: str, limit: int, window_seconds: int):
    """
    FastAPI dependency factory. Use as `Depends(rate_limit("login", settings.rate_limit.login_limit, 60))`.
    """

    def _dependency(request: Request) -> None:
        if not settings.rate_limit.enabled:
            return

        client = _get_client()
        if client is None:
            return

        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{category}:{client_ip}"

        try:
            count = client.incr(key)
            if count == 1:
                client.expire(key, window_seconds)
        except Exception:
            global _unavailable_logged
            if not _unavailable_logged:
                logger.warning("Rate limiter Redis unavailable - failing open for category=%s", category)
                _unavailable_logged = True
            return

        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again in a moment.",
            )

    return _dependency
