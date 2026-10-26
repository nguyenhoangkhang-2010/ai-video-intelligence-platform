from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.metrics import (
    HTTP_REQUESTS_TOTAL,
    PROCESSING_JOBS_ACTIVE,
    render_metrics,
    setup_metrics_middleware,
    update_processing_jobs_gauge,
)


def _make_app():
    app = FastAPI()
    setup_metrics_middleware(app)

    @app.get("/videos/{video_id}")
    def get_video(video_id: int):
        return {"video_id": video_id}

    return app


def test_render_metrics_returns_bytes_and_prometheus_content_type():
    body, content_type = render_metrics()

    assert isinstance(body, bytes)
    assert "text/plain" in content_type


def test_middleware_records_route_path_template_not_resolved_path():
    app = _make_app()
    client = TestClient(app)

    client.get("/videos/1")
    client.get("/videos/2")

    body = render_metrics()[0].decode()

    # Both calls collapse onto the route template - not one series per id.
    assert 'path="/videos/{video_id}"' in body
    assert 'path="/videos/1"' not in body
    assert 'path="/videos/2"' not in body


def test_middleware_records_request_count_and_status_code():
    app = _make_app()
    client = TestClient(app)

    HTTP_REQUESTS_TOTAL.labels(
        method="GET", path="/videos/{video_id}", status_code=200,
    )._value.set(0)

    client.get("/videos/1")

    body = render_metrics()[0].decode()
    assert 'method="GET"' in body
    assert 'status_code="200"' in body


def test_update_processing_jobs_gauge_sets_value_from_query():
    db = MagicMock()
    db.query.return_value.filter.return_value.scalar.return_value = 3

    update_processing_jobs_gauge(db)

    assert PROCESSING_JOBS_ACTIVE._value.get() == 3


def test_update_processing_jobs_gauge_handles_db_error_gracefully():
    db = MagicMock()
    db.query.return_value.filter.return_value.scalar.side_effect = RuntimeError("db down")

    # Must not raise - a DB hiccup should not take down /metrics.
    update_processing_jobs_gauge(db)
