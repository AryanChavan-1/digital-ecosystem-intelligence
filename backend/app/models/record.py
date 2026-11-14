import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Numeric, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SourceRecord(Base):
    __tablename__ = "source_records"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("data_sources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True
    )
    external_record_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    canonical_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    local_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    language_code: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    spam_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4), nullable=True)
    permission_status: Mapped[str] = mapped_column(
        String(50), default="approved", nullable=False
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB().with_variant(JSON, "sqlite"), nullable=True, default=dict
    )
