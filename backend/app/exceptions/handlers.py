"""
Global exception handling.

FastAPI/Starlette already handle the common, expected cases
correctly and consistently on their own:
  - HTTPException (401/403/404/409/... raised throughout
    app/services/*) -> a clean {"detail": "..."} JSON response with
    the given status code.
  - RequestValidationError (422, invalid request body/params) -> a
    structured {"detail": [...]} JSON response describing exactly
    which fields failed.
  - In production (ENVIRONMENT/DEBUG=False - see
    deployment/docker/docker-compose.prod.yml), Starlette's own
    ServerErrorMiddleware already suppresses tracebacks for anything
    unhandled.

The one real gap: that last case returns a *plain-text*
"Internal Server Error" body, not the {"detail": "..."} JSON shape
every other error response in this API uses, and it doesn't go
through this application's own structured logging (app.config.
logging). This handler closes exactly that gap - it is intentionally
the only handler here; it does not reimplement anything FastAPI
already does correctly, and does not introduce a second custom
exception hierarchy (see app/exceptions/custom_exceptions.py, left
empty - every existing raise site already uses HTTPException
directly and consistently; there is nothing to migrate).
"""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Last-resort handler for any exception that reaches here unhandled
    (i.e. not an HTTPException/RequestValidationError, both already
    handled by FastAPI itself). Logs the real exception server-side
    (via this app's own logging - request_id-correlated, see
    app.config.logging) and returns a generic, detail-free 500 to the
    client - never a stack trace, database error text, filesystem
    path, or any other internal detail.
    """
    logger.exception(
        "Unhandled exception while processing %s %s",
        request.method,
        request.url.path,
    )

    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


def setup_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )
