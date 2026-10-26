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

Two real gaps this module closes:

1. app.core.exceptions.AppException and its subclasses
   (InvalidCredentialsError, UserAlreadyExistsError,
   VideoNotFoundError, InactiveUserError) are raised in a few places
   (e.g. AuthService.login/register) but were never mapped to an HTTP
   status code anywhere - nothing caught them, so they fell all the
   way through to the generic 500 handler below, turning "wrong
   password" and "email already registered" into an opaque server
   error instead of 401/409. app_exception_handler fixes exactly
   that, with no change to where/why these are raised.
2. Anything else unhandled previously returned a *plain-text*
   "Internal Server Error" body, not the {"detail": "..."} JSON shape
   every other error response in this API uses, and didn't go through
   this application's own structured logging (app.config.logging).
   unhandled_exception_handler closes that gap.

Neither handler reimplements anything FastAPI already does correctly,
and this does not introduce a second, competing exception hierarchy -
app.core.exceptions.AppException already existed and was already in
real use; it just had no handler until now. app/exceptions/
custom_exceptions.py remains intentionally empty (see that file) -
every *other* raise site already uses HTTPException directly and
consistently; there is nothing further to migrate.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AppException,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidJobStatusTransitionError,
    UserAlreadyExistsError,
    VideoNotFoundError,
)

logger = logging.getLogger(__name__)

_APP_EXCEPTION_STATUS_CODES: dict[type[AppException], int] = {
    InvalidCredentialsError: 401,
    UserAlreadyExistsError: 409,
    VideoNotFoundError: 404,
    InactiveUserError: 403,
    InvalidJobStatusTransitionError: 409,
}
_DEFAULT_APP_EXCEPTION_STATUS_CODE = 400


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    """
    Maps a known app.core.exceptions.AppException subclass to its
    HTTP status code and the same {"detail": "..."} shape every other
    error response in this API already uses. An AppException subclass
    with no explicit mapping falls back to 400 (a caller-facing
    business-rule rejection is a far more likely explanation than a
    genuine 500 for anything deliberately raised as an AppException)
    rather than silently becoming a 500.
    """
    status_code = _APP_EXCEPTION_STATUS_CODES.get(
        type(exc), _DEFAULT_APP_EXCEPTION_STATUS_CODE,
    )

    return JSONResponse(
        status_code=status_code,
        content={"detail": str(exc)},
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Last-resort handler for any exception that reaches here unhandled
    (i.e. not an HTTPException/RequestValidationError/AppException,
    all already handled above/by FastAPI itself). Logs the real
    exception server-side (via this app's own logging - request_id-
    correlated, see app.config.logging) and returns a generic,
    detail-free 500 to the client - never a stack trace, database
    error text, filesystem path, or any other internal detail.
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
        AppException,
        app_exception_handler,
    )
    app.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )
