"""
Request ID middleware.

Adds unique ID for every request.
"""
import uuid
from fastapi import FastAPI, Request

from app.config.logging import request_id_var

REQUEST_ID_HEADER = "X-Request-ID"

def setup_request_id_middleware(
    app: FastAPI
) -> None:
    @app.middleware("http")
    async def request_id_middleware(
        request: Request,
        call_next
    ):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Also published to a contextvar so every log line emitted
        # while handling this request - not just the one line
        # app.middleware.logging prints - is tagged with it (see
        # app.config.logging.ContextFilter).
        token = request_id_var.set(request_id)

        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)

        response.headers[
            REQUEST_ID_HEADER
        ] = request_id
        return response