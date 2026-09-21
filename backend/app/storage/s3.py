"""
Optional S3-compatible StorageBackend implementation (AWS S3 or any
S3-compatible endpoint such as MinIO, via STORAGE_S3_ENDPOINT_URL).

boto3 is already a listed/installed project dependency; it is still
imported lazily here (only when this backend is actually
instantiated, mirroring the lazy-import convention already used for
other optional/heavy dependencies in this codebase - e.g.
ai.reranking.cross_encoder.CrossEncoderReranker for
sentence-transformers) so that importing app.storage - or the whole
application - never requires boto3 to be configured/reachable, and
selecting STORAGE_BACKEND=local (the default) never touches this
module at all.

Credentials are resolved by boto3's standard chain
(AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY env vars, shared credentials
file, or an IAM role) - no custom credential settings are introduced
here, and none are ever logged.
"""
import logging

from app.config.settings import settings

logger = logging.getLogger(__name__)


class S3StorageBackend:
    """StorageBackend implementation backed by an S3-compatible bucket."""

    def __init__(
        self,
        bucket: str | None = None,
        endpoint_url: str | None = None,
        region_name: str | None = None,
    ):
        import boto3

        self.bucket = bucket or settings.storage.s3_bucket
        if not self.bucket:
            raise ValueError(
                "S3StorageBackend requires a bucket name "
                "(STORAGE_S3_BUCKET)."
            )

        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url or settings.storage.s3_endpoint_url,
            region_name=region_name or settings.storage.s3_region,
        )

    def save(self, key: str, data: bytes) -> str:
        self._client.put_object(Bucket=self.bucket, Key=key, Body=data)
        return f"s3://{self.bucket}/{key}"

    def read(self, key: str) -> bytes:
        response = self._client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") in ("404", "NoSuchKey"):
                return False
            raise

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self.bucket, Key=key)

    def get_local_path(self, key: str):
        # No real filesystem path for an S3 object.
        return None

    def get_url(self, key: str, expires_in: int = 3600) -> str | None:
        """
        Presigned, time-limited GET URL - lets a client (browser
        <video> element, HTTP client) fetch the object directly from
        S3/MinIO, including Range-request support for seeking, without
        proxying the bytes through this application.
        """
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )
