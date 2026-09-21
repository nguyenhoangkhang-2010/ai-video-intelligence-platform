from unittest.mock import MagicMock, patch

import pytest

from app.storage.s3 import S3StorageBackend


def _make_backend(mock_client):
    with patch("boto3.client", return_value=mock_client):
        return S3StorageBackend(bucket="test-bucket")


def test_constructor_requires_a_bucket():
    with patch("boto3.client", return_value=MagicMock()):
        with pytest.raises(ValueError):
            S3StorageBackend(bucket=None)


def test_save_calls_put_object():
    mock_client = MagicMock()
    backend = _make_backend(mock_client)

    locator = backend.save("videos/1/source.mp4", b"data")

    mock_client.put_object.assert_called_once_with(
        Bucket="test-bucket", Key="videos/1/source.mp4", Body=b"data",
    )
    assert locator == "s3://test-bucket/videos/1/source.mp4"


def test_read_returns_object_body_bytes():
    mock_client = MagicMock()
    mock_body = MagicMock()
    mock_body.read.return_value = b"downloaded bytes"
    mock_client.get_object.return_value = {"Body": mock_body}
    backend = _make_backend(mock_client)

    result = backend.read("key.txt")

    assert result == b"downloaded bytes"
    mock_client.get_object.assert_called_once_with(Bucket="test-bucket", Key="key.txt")


def test_delete_calls_delete_object():
    mock_client = MagicMock()
    backend = _make_backend(mock_client)

    backend.delete("key.txt")

    mock_client.delete_object.assert_called_once_with(Bucket="test-bucket", Key="key.txt")


def test_exists_true_when_head_object_succeeds():
    mock_client = MagicMock()
    mock_client.head_object.return_value = {}
    backend = _make_backend(mock_client)

    assert backend.exists("key.txt") is True


def test_exists_false_when_head_object_raises_404():
    from botocore.exceptions import ClientError

    mock_client = MagicMock()
    mock_client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}}, "HeadObject",
    )
    backend = _make_backend(mock_client)

    assert backend.exists("key.txt") is False


def test_exists_reraises_non_404_client_errors():
    from botocore.exceptions import ClientError

    mock_client = MagicMock()
    mock_client.head_object.side_effect = ClientError(
        {"Error": {"Code": "403", "Message": "Forbidden"}}, "HeadObject",
    )
    backend = _make_backend(mock_client)

    with pytest.raises(ClientError):
        backend.exists("key.txt")
