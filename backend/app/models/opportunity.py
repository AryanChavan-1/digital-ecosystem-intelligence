import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.topic import Topic

if TYPE_CHECKING:
    from app.models.report import Report


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("topics.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    score: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    evidence: Mapped[Optional[dict]] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"), default=dict, nullable=True
    )
    limitations: Mapped[Optional[dict]] = mapped_column(
        JSONB().with_variant(JSON, "sqlite"), default=dict, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    topic: Mapped[Optional["Topic"]] = relationship("Topic")
    reports: Mapped[List["Report"]] = relationship("Report", back_populates="opportunity")
