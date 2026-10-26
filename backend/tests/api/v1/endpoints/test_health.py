from unittest.mock import MagicMock

from app.api.v1.endpoints.health import health_check, liveness_check, readiness_check


def test_health_check_returns_ok_when_database_reachable():
    db = MagicMock()
    db.execute.return_value = None

    result = health_check(db=db)

    assert result == {"status": "ok", "database": "connected"}
    db.execute.assert_called_once()


def test_health_check_returns_503_when_database_unreachable():
    db = MagicMock()
    db.execute.side_effect = RuntimeError("connection refused")

    response = health_check(db=db)

    assert response.status_code == 503


def test_liveness_check_never_touches_the_database():
    # No db fixture/argument at all - liveness must be independent of
    # every dependency, so a DB outage can never fail a liveness probe.
    result = liveness_check()

    assert result == {"status": "ok"}


def test_readiness_check_returns_ok_when_database_reachable():
    db = MagicMock()
    db.execute.return_value = None

    result = readiness_check(db=db)

    assert result == {"status": "ok", "database": "connected"}


def test_readiness_check_returns_503_when_database_unreachable():
    db = MagicMock()
    db.execute.side_effect = RuntimeError("connection refused")

    response = readiness_check(db=db)

    assert response.status_code == 503
