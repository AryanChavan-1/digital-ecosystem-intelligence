import uuid
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.errors import PayloadTooLargeException

MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB


def generate_object_key(
    workspace_id: uuid.UUID | str,
    upload_id: uuid.UUID | str,
    extension: str = "csv",
) -> str:
    """
    Generate deterministic, safe UUID-based storage key.
    Never trust user-supplied original_filename as a storage path.
    """
    ext = extension.lstrip(".") if extension else "csv"
    return f"workspaces/{workspace_id}/uploads/{upload_id}.{ext}"


class BaseStorageAdapter(ABC):
    @abstractmethod
    def generate_upload_url(self, object_key: str, expires_in: int = 3600) -> str:
        """Generate presigned upload URL."""
        pass

    @abstractmethod
    def generate_download_url(self, object_key: str, expires_in: int = 3600) -> str:
        """Generate presigned download URL."""
        pass

    @abstractmethod
    def put_object(self, object_key: str, data: bytes) -> None:
        """Store binary data directly."""
        pass

    @abstractmethod
    def get_object(self, object_key: str) -> bytes:
        """Retrieve binary data."""
        pass

    @abstractmethod
    def get_object_size(self, object_key: str) -> int:
        """Get object size in bytes."""
        pass

    @abstractmethod
    def object_exists(self, object_key: str) -> bool:
        """Check if object exists."""
        pass

    @abstractmethod
    def delete_object(self, object_key: str) -> None:
        """Delete object."""
        pass


class LocalFilesystemAdapter(BaseStorageAdapter):
    def __init__(self, base_dir: str = "./.local_storage"):
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, object_key: str) -> Path:
        clean_key = object_key.replace("\\", "/").lstrip("/")
        full_path = (self.base_dir / clean_key).resolve()
        # Security check to prevent path traversal
        if not str(full_path).startswith(str(self.base_dir)):
            raise ValueError(f"Path traversal detected for object_key: {object_key}")
        return full_path

    def generate_upload_url(self, object_key: str, expires_in: int = 3600) -> str:
        clean_key = object_key.replace("\\", "/").lstrip("/")
        return f"{settings.API_V1_PREFIX}/uploads/local-storage/{clean_key}"

    def generate_download_url(self, object_key: str, expires_in: int = 3600) -> str:
        clean_key = object_key.replace("\\", "/").lstrip("/")
        return f"{settings.API_V1_PREFIX}/uploads/local-storage/{clean_key}"

    def put_object(self, object_key: str, data: bytes) -> None:
        if len(data) > MAX_UPLOAD_SIZE_BYTES:
            raise PayloadTooLargeException()
        target_path = self._resolve_path(object_key)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(data)

    def get_object(self, object_key: str) -> bytes:
        target_path = self._resolve_path(object_key)
        if not target_path.exists():
            raise FileNotFoundError(f"Storage object not found: {object_key}")
        return target_path.read_bytes()

    def get_object_size(self, object_key: str) -> int:
        target_path = self._resolve_path(object_key)
        if not target_path.exists():
            raise FileNotFoundError(f"Storage object not found: {object_key}")
        return target_path.stat().st_size

    def object_exists(self, object_key: str) -> bool:
        return self._resolve_path(object_key).exists()

    def delete_object(self, object_key: str) -> None:
        target_path = self._resolve_path(object_key)
        if target_path.exists():
            target_path.unlink()


class S3StorageAdapter(BaseStorageAdapter):
    def __init__(
        self,
        bucket_name: str,
        endpoint_url: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        region: str = "auto",
    ):
        import boto3
        from botocore.config import Config

        self.bucket_name = bucket_name
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region if region != "auto" else None,
            config=Config(signature_version="s3v4"),
        )

    def generate_upload_url(self, object_key: str, expires_in: int = 3600) -> str:
        return self.s3_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": self.bucket_name, "Key": object_key},
            ExpiresIn=expires_in,
        )

    def generate_download_url(self, object_key: str, expires_in: int = 3600) -> str:
        return self.s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": object_key},
            ExpiresIn=expires_in,
        )

    def put_object(self, object_key: str, data: bytes) -> None:
        if len(data) > MAX_UPLOAD_SIZE_BYTES:
            raise PayloadTooLargeException()
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=object_key,
            Body=data,
        )

    def get_object(self, object_key: str) -> bytes:
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=object_key)
        return response["Body"].read()

    def get_object_size(self, object_key: str) -> int:
        response = self.s3_client.head_object(Bucket=self.bucket_name, Key=object_key)
        return response["ContentLength"]

    def object_exists(self, object_key: str) -> bool:
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except Exception:
            return False

    def delete_object(self, object_key: str) -> None:
        self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)


class StorageService:
    def __init__(self, adapter: Optional[BaseStorageAdapter] = None):
        if adapter is not None:
            self.adapter = adapter
        elif settings.STORAGE_MODE == "s3" and settings.S3_BUCKET_NAME:
            self.adapter = S3StorageAdapter(
                bucket_name=settings.S3_BUCKET_NAME,
                endpoint_url=settings.S3_ENDPOINT_URL,
                access_key_id=settings.S3_ACCESS_KEY_ID,
                secret_access_key=settings.S3_SECRET_ACCESS_KEY,
                region=settings.S3_REGION,
            )
        else:
            self.adapter = LocalFilesystemAdapter(base_dir=settings.LOCAL_STORAGE_DIR)

    def validate_file_size(self, file_size_bytes: Optional[int]) -> None:
        if file_size_bytes is not None and file_size_bytes > MAX_UPLOAD_SIZE_BYTES:
            raise PayloadTooLargeException()

    def generate_object_key(
        self,
        workspace_id: uuid.UUID | str,
        upload_id: uuid.UUID | str,
        extension: str = "csv",
    ) -> str:
        return generate_object_key(workspace_id, upload_id, extension)

    def generate_upload_url(self, object_key: str, expires_in: int = 3600) -> str:
        return self.adapter.generate_upload_url(object_key, expires_in=expires_in)

    def generate_download_url(self, object_key: str, expires_in: int = 3600) -> str:
        return self.adapter.generate_download_url(object_key, expires_in=expires_in)

    def put_object(self, object_key: str, data: bytes) -> None:
        self.validate_file_size(len(data))
        self.adapter.put_object(object_key, data)

    def get_object(self, object_key: str) -> bytes:
        return self.adapter.get_object(object_key)

    def get_object_size(self, object_key: str) -> int:
        return self.adapter.get_object_size(object_key)

    def object_exists(self, object_key: str) -> bool:
        return self.adapter.object_exists(object_key)

    def delete_object(self, object_key: str) -> None:
        self.adapter.delete_object(object_key)


_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
