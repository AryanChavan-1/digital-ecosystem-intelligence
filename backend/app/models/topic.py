import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.trend import TrendSnapshot


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True
    )
    canonical_label: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language_code: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    aliases: Mapped[List["TopicAlias"]] = relationship(
        "TopicAlias", back_populates="topic", cascade="all, delete-orphan"
    )
    snapshots: Mapped[List["TrendSnapshot"]] = relationship(
        "TrendSnapshot", back_populates="topic", cascade="all, delete-orphan"
    )


class TopicAlias(Base):
    __tablename__ = "topic_aliases"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    alias: Mapped[str] = mapped_column(String(255), nullable=False)
    language_code: Mapped[str] = mapped_column(String(10), default="en", nullable=False)

    topic: Mapped["Topic"] = relationship("Topic", back_populates="aliases")


class TopicRecordAssignment(Base):
    __tablename__ = "topic_record_assignments"

    topic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )
    source_record_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("source_records.id", ondelete="CASCADE"), primary_key=True
    )
    assignment_score: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("1.0000"), nullable=False
    )
    model_version: Mapped[str] = mapped_column(
        String(50), primary_key=True, default="v1.0"
    )


class TopicRelation(Base):
    __tablename__ = "topic_relations"

    source_topic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )
    target_topic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )
    relation_type: Mapped[str] = mapped_column(
        String(50), primary_key=True, default="co_occurs"
    )
    weight: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("1.0000"), nullable=False
    )
    window_start: Mapped[date] = mapped_column(Date, primary_key=True)
    window_end: Mapped[date] = mapped_column(Date, nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), default="v1.0", nullable=False)
