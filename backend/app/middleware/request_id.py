"""
Request ID middleware.

Adds unique ID for every request.
"""
import uuid
from fastapi import FastAPI, Request

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
        response = await call_next(request)
        response.headers[
            REQUEST_ID_HEADER
        ] = request_id
        return response