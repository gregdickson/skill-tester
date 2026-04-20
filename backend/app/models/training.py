import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TrainingRun(Base):
    __tablename__ = "training_run"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    network_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("network.id", ondelete="CASCADE"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="running")
    total_steps: Mapped[int] = mapped_column(Integer, default=0)
    loss_start: Mapped[float | None] = mapped_column(Float)
    loss_end: Mapped[float | None] = mapped_column(Float)
    loss_history: Mapped[list] = mapped_column(JSONB, default=list)
    improvements: Mapped[dict] = mapped_column(JSONB, default=dict)
    config_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_seconds: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        CheckConstraint("status IN ('running', 'complete', 'failed', 'paused')", name="ck_training_run_status"),
    )

    network: Mapped["Network"] = relationship(back_populates="training_runs")
    evaluations: Mapped[list["Evaluation"]] = relationship(back_populates="training_run")


class Evaluation(Base):
    __tablename__ = "evaluation"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    training_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("training_run.id", ondelete="CASCADE"), nullable=False, index=True)
    component_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("component.id", ondelete="CASCADE"), nullable=False, index=True)
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    nudge_direction: Mapped[str] = mapped_column(String(8), nullable=False)
    nudge_delta: Mapped[float | None] = mapped_column(Float)
    score_before: Mapped[float | None] = mapped_column(Float)
    score_after: Mapped[float | None] = mapped_column(Float)
    evaluator_notes: Mapped[str | None] = mapped_column(Text)
    research_performed: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("nudge_direction IN ('baseline', 'up', 'down')", name="ck_evaluation_direction"),
    )

    training_run: Mapped["TrainingRun"] = relationship(back_populates="evaluations")
    component: Mapped["Component"] = relationship(back_populates="evaluations")
