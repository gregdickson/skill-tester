import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Component(Base):
    __tablename__ = "component"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    network_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("network.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, default="medium")
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    initial_weight: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    score_pct: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(15), nullable=False, default="developing")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sub_components: Mapped[list] = mapped_column(JSONB, default=list)
    research_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint("priority IN ('critical', 'high', 'medium', 'low')", name="ck_component_priority"),
        CheckConstraint("status IN ('strong', 'developing', 'weak')", name="ck_component_status"),
    )

    network: Mapped["Network"] = relationship(back_populates="components")
    evaluations: Mapped[list["Evaluation"]] = relationship(back_populates="component")
