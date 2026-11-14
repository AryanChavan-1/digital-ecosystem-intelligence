import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.topic import Topic


class AudienceCluster(Base):
    __tablename__ = "audience_clusters"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dataset_version: Mapped[str] = mapped_column(String(50), default="v1.0", nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), default="v1.0", nullable=False)
    record_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quality_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    is_user_renamed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    label_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    cluster_topics: Mapped[List["ClusterTopic"]] = relationship(
        "ClusterTopic", back_populates="cluster", cascade="all, delete-orphan"
    )


class ClusterTopic(Base):
    __tablename__ = "cluster_topics"

    cluster_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("audience_clusters.id", ondelete="CASCADE"), primary_key=True
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )
    weight: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("1.0000"), nullable=False
    )

    cluster: Mapped["AudienceCluster"] = relationship("AudienceCluster", back_populates="cluster_topics")
    topic: Mapped["Topic"] = relationship("Topic")
