import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, Integer, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Network(Base):
    __tablename__ = "network"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str | None] = mapped_column(Text)
    ultimate_end_goal: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    mode: Mapped[str] = mapped_column(String(10), nullable=False, default="learn")
    readiness_pct: Mapped[float] = mapped_column(Float, default=0.0)
    current_loss: Mapped[float | None] = mapped_column(Float)
    total_steps: Mapped[int] = mapped_column(Integer, default=0)
    network_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    how_it_works: Mapped[str | None] = mapped_column(Text)
    reference_files: Mapped[list] = mapped_column(JSONB, default=list)
    learning_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    command_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('draft', 'training', 'converged', 'archived')", name="ck_network_status"),
        CheckConstraint("mode IN ('learn', 'command')", name="ck_network_mode"),
    )

    company: Mapped["Company"] = relationship(back_populates="networks")
    components: Mapped[list["Component"]] = relationship(back_populates="network", order_by="Component.sort_order")
    training_runs: Mapped[list["TrainingRun"]] = relationship(back_populates="network")
    outputs: Mapped[list["GeneratedOutput"]] = relationship(back_populates="network")
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="network")
    activity_logs: Mapped[list["ActivityLog"]] = relationship(back_populates="network")
