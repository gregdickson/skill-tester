import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OutputTemplate(Base):
    __tablename__ = "output_template"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    network_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("network.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    output_type: Mapped[str] = mapped_column(String(30), nullable=False, default="skill_md")
    master_rule: Mapped[str | None] = mapped_column(Text)
    prompt_template: Mapped[str | None] = mapped_column(Text)
    format_rules: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        CheckConstraint(
            "output_type IN ('skill_md', 'agent_config', 'python_script', 'process_doc', "
            "'architecture_diagram', 'email_outreach', 'ad_copy', 'custom')",
            name="ck_output_template_type",
        ),
    )


class GeneratedOutput(Base):
    __tablename__ = "generated_output"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    network_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("network.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("output_template.id", ondelete="SET NULL"))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    weights_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict)
    quality_score: Mapped[float | None] = mapped_column(Float)
    human_score: Mapped[float | None] = mapped_column(Float)
    pushed_to: Mapped[str | None] = mapped_column(String(500))
    pushed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    network: Mapped["Network"] = relationship(back_populates="outputs")
