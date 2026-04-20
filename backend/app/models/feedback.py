import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    network_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("network.id", ondelete="CASCADE"), nullable=False, index=True)
    output_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("generated_output.id", ondelete="SET NULL"))
    source: Mapped[str] = mapped_column(String(15), nullable=False, default="manual")
    feedback_type: Mapped[str] = mapped_column(String(10), nullable=False, default="neutral")
    metric_name: Mapped[str | None] = mapped_column(String(255))
    metric_value: Mapped[float | None] = mapped_column(Float)
    notes: Mapped[str | None] = mapped_column(Text)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("source IN ('manual', 'webhook', 'metric', 'agent_report')", name="ck_feedback_source"),
        CheckConstraint("feedback_type IN ('positive', 'negative', 'neutral', 'metric')", name="ck_feedback_type"),
    )

    network: Mapped["Network"] = relationship(back_populates="feedback")
