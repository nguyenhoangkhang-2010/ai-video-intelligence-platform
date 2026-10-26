"""
Baseline security response headers.

Deliberately does NOT set Content-Security-Policy here - this backend
serves a JSON API plus a video byte stream, never rendered HTML for
real end users (the only HTML this process ever serves is the dev-only
Swagger/ReDoc UI at /docs and /redoc, which pull their own assets from
a CDN and would need a carefully scoped, separately-tested CSP of
their own to avoid breaking). The headers below are safe on every
response regardless of content type - none of them restrict what a
JSON response body or a video byte range can contain.
"""
from fastapi import FastAPI


def setup_security_headers_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def security_headers_middleware(request, call_next):
        response = await call_next(request)

        # Stops a browser from MIME-sniffing a response into executing
        # as something other than its declared Content-Type.
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Never send the full referring URL (which could contain a
        # video id, search query, etc.) to a third-party origin -
        # same-origin navigations still get the full path.
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # This API is never meant to be framed by another site.
        response.headers["X-Frame-Options"] = "DENY"

        # Deny browser features this API has no legitimate use for.
        # Left deliberately short - only features this backend could
        # never need, not a blanket denial that might surprise a
        # future legitimate use.
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

        return response
