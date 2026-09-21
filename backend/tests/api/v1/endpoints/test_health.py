from unittest.mock import MagicMock

from app.api.v1.endpoints.health import health_check


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
