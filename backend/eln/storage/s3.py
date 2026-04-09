from pathlib import Path

from eln.storage.base import StorageBackend


class S3StorageBackend(StorageBackend):
    """Stores objects in S3-compatible object storage (AWS S3 or MinIO).

    Set endpoint_url to None for AWS S3, or e.g. "http://localhost:9000"
    for a local MinIO instance.
    """

    def __init__(
        self,
        bucket: str,
        endpoint_url: str = "",
        access_key_id: str = "",
        secret_access_key: str = "",
        region: str = "us-east-1",
        presign_expires: int = 3600,
    ) -> None:
        import boto3
        from botocore.config import Config

        self.bucket = bucket
        self.presign_expires = presign_expires

        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url or None,
            aws_access_key_id=access_key_id or None,
            aws_secret_access_key=secret_access_key or None,
            region_name=region,
            config=Config(signature_version="s3v4"),
        )
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        from botocore.exceptions import ClientError

        try:
            self._client.head_bucket(Bucket=self.bucket)
        except ClientError as e:
            code = e.response["Error"]["Code"]
            if code in ("404", "NoSuchBucket"):
                self._client.create_bucket(Bucket=self.bucket)

    def put_object(self, key: str, source_path: Path) -> str:
        self._client.upload_file(str(source_path), self.bucket, key)
        return key

    def get_object(self, key: str, dest_path: Path) -> None:
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        self._client.download_file(self.bucket, key, str(dest_path))

    def get_url(self, key: str, expires_in: int = 3600) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def exists(self, key: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self._client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False

    def delete(self, key: str) -> None:
        self._client.delete_object(Bucket=self.bucket, Key=key)
