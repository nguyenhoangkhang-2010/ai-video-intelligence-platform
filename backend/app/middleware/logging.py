"""
HTTP request logging middleware.
"""
import time
import logging

from fastapi import FastAPI, Request

logger = logging.getLogger(
    "api"
)

def setup_logging_middleware(
    app: FastAPI
) -> None:

    @app.middleware("http")
    async def logging_middleware(
        request: Request,
        call_next
    ):
        start_time = time.time()

        response = await call_next(
            request
        )

        process_time = (
            time.time()
            - start_time
        )

        logger.info(
            "%s %s - %s - %.4fs",
            request.method,
            request.url.path,
            response.status_code,
            process_time
        )

        return response