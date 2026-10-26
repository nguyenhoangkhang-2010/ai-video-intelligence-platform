import redis.exceptions
import requests.exceptions
from sqlalchemy.exc import OperationalError

from app.core.retry import is_transient_error


def test_is_transient_error_true_for_db_operational_error():
    exc = OperationalError("stmt", {}, Exception("connection refused"))
    assert is_transient_error(exc) is True


def test_is_transient_error_true_for_redis_connection_error():
    assert is_transient_error(redis.exceptions.ConnectionError()) is True


def test_is_transient_error_true_for_requests_connection_error():
    assert is_transient_error(requests.exceptions.ConnectionError()) is True


def test_is_transient_error_true_for_requests_timeout():
    assert is_transient_error(requests.exceptions.Timeout()) is True


def test_is_transient_error_true_for_generic_connection_error():
    assert is_transient_error(ConnectionError()) is True


def test_is_transient_error_false_for_value_error():
    # A deterministic application/data error - retrying would not help.
    assert is_transient_error(ValueError("no speech detected")) is False


def test_is_transient_error_false_for_key_error():
    assert is_transient_error(KeyError("missing field")) is False


def test_is_transient_error_false_for_http_error():
    # A well-formed request rejected by the server (e.g. 4xx) - not
    # a connectivity problem, retrying identically won't change it.
    assert is_transient_error(requests.exceptions.HTTPError()) is False
