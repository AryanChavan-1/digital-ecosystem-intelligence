import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, Numeric, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.topic import Topic


class TrendSnapshot(Base):
    __tablename__ = "trend_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4
    )
    workspace_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=True, index=True
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    mention_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    previous_mention_count: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    change_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), nullable=True)
    momentum_score: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("0.0000"), nullable=False, index=True
    )
    source_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    confidence: Mapped[str] = mapped_column(String(50), default="medium", nullable=False)
    feature_version: Mapped[str] = mapped_column(String(50), default="v1.0", nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), default="v1.0", nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    topic: Mapped["Topic"] = relationship("Topic", back_populates="snapshots")
