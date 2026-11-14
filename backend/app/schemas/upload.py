import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UploadCreateRequest(BaseModel):
    filename: str = Field(..., description="Original filename of the CSV export")
    file_size_bytes: Optional[int] = Field(None, description="Size in bytes, max 25MB")

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Filename cannot be empty")
        if not clean.lower().endswith(".csv"):
            raise ValueError("Only CSV files (.csv) are supported")
        return clean

    @field_validator("file_size_bytes")
    @classmethod
    def validate_file_size(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            max_size = 25 * 1024 * 1024  # 25 MB
            if v <= 0:
                raise ValueError("File size must be positive")
            if v > max_size:
                raise ValueError("File size exceeds 25 MB limit")
        return v


class UploadCreateResponseData(BaseModel):
    upload_id: uuid.UUID
    upload_url: str
    object_key: str


class UploadConfirmRequest(BaseModel):
    mapping: Dict[str, str] = Field(
        ...,
        description="Column mapping connecting canonical fields to CSV headers",
    )
    date_format: Optional[str] = Field(
        None,
        description="Explicit date format hint (e.g. DD/MM/YYYY or %d/%m/%Y)",
    )


class UploadDetailResponseData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    uploaded_by: Optional[uuid.UUID] = None
    object_key: str
    original_filename: str
    checksum_sha256: Optional[str] = None
    file_size_bytes: Optional[int] = None
    status: str
    mapping: Optional[Dict[str, Any]] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_summary: Optional[Dict[str, Any]] = None
