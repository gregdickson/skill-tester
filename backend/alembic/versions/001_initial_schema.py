"""Initial schema with all tables

Revision ID: 001
Revises:
Create Date: 2026-04-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Company
    op.create_table(
        "company",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("paperclip_config", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Company Brain
    op.create_table(
        "company_brain",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("company.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("knowledge_base", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("cross_references", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("last_synthesis", sa.DateTime(timezone=True)),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Network
    op.create_table(
        "network",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("company.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("purpose", sa.Text),
        sa.Column("ultimate_end_goal", sa.Text, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("mode", sa.String(10), nullable=False, server_default="learn"),
        sa.Column("readiness_pct", sa.Float, server_default="0.0"),
        sa.Column("current_loss", sa.Float),
        sa.Column("total_steps", sa.Integer, server_default="0"),
        sa.Column("network_config", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("how_it_works", sa.Text),
        sa.Column("reference_files", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("learning_config", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("command_config", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("status IN ('draft', 'training', 'converged', 'archived')", name="ck_network_status"),
        sa.CheckConstraint("mode IN ('learn', 'command')", name="ck_network_mode"),
    )

    # Component
    op.create_table(
        "component",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("network_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("network.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("priority", sa.String(10), nullable=False, server_default="medium"),
        sa.Column("weight", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("initial_weight", sa.Float, nullable=False, server_default="0.5"),
        sa.Column("score_pct", sa.Float, server_default="0.0"),
        sa.Column("status", sa.String(15), nullable=False, server_default="developing"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("sub_components", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("research_notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("priority IN ('critical', 'high', 'medium', 'low')", name="ck_component_priority"),
        sa.CheckConstraint("status IN ('strong', 'developing', 'weak')", name="ck_component_status"),
    )
    op.create_index("idx_component_network", "component", ["network_id"])
    op.create_index("idx_component_sort", "component", ["network_id", "sort_order"])

    # Training Run
    op.create_table(
        "training_run",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("network_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("network.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("status", sa.String(10), nullable=False, server_default="running"),
        sa.Column("total_steps", sa.Integer, server_default="0"),
        sa.Column("loss_start", sa.Float),
        sa.Column("loss_end", sa.Float),
        sa.Column("loss_history", postgresql.JSONB, server_default=sa.text("'[]'::jsonb")),
        sa.Column("improvements", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("config_snapshot", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("duration_seconds", sa.Integer),
        sa.CheckConstraint("status IN ('running', 'complete', 'failed', 'paused')", name="ck_training_run_status"),
    )
    op.create_index("idx_training_run_network", "training_run", ["network_id"])

    # Evaluation
    op.create_table(
        "evaluation",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("training_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("training_run.id", ondelete="CASCADE"), nullable=False),
        sa.Column("component_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("component.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_number", sa.Integer, nullable=False),
        sa.Column("nudge_direction", sa.String(8), nullable=False),
        sa.Column("nudge_delta", sa.Float),
        sa.Column("score_before", sa.Float),
        sa.Column("score_after", sa.Float),
        sa.Column("evaluator_notes", sa.Text),
        sa.Column("research_performed", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("nudge_direction IN ('baseline', 'up', 'down')", name="ck_evaluation_direction"),
    )
    op.create_index("idx_evaluation_run", "evaluation", ["training_run_id"])
    op.create_index("idx_evaluation_component", "evaluation", ["component_id"])

    # Output Template
    op.create_table(
        "output_template",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("network_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("network.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("output_type", sa.String(30), nullable=False, server_default="skill_md"),
        sa.Column("master_rule", sa.Text),
        sa.Column("prompt_template", sa.Text),
        sa.Column("format_rules", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "output_type IN ('skill_md', 'agent_config', 'python_script', 'process_doc', "
            "'architecture_diagram', 'email_outreach', 'ad_copy', 'custom')",
            name="ck_output_template_type",
        ),
    )

    # Generated Output
    op.create_table(
        "generated_output",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("network_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("network.id", ondelete="CASCADE"), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("output_template.id", ondelete="SET NULL")),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("weights_snapshot", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("quality_score", sa.Float),
        sa.Column("human_score", sa.Float),
        sa.Column("pushed_to", sa.String(500)),
        sa.Column("pushed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_generated_output_network", "generated_output", ["network_id"])

    # Feedback
    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("network_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("network.id", ondelete="CASCADE"), nullable=False),
        sa.Column("output_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("generated_output.id", ondelete="SET NULL")),
        sa.Column("source", sa.String(15), nullable=False, server_default="manual"),
        sa.Column("feedback_type", sa.String(10), nullable=False, server_default="neutral"),
        sa.Column("metric_name", sa.String(255)),
        sa.Column("metric_value", sa.Float),
        sa.Column("notes", sa.Text),
        sa.Column("processed", sa.Boolean, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("source IN ('manual', 'webhook', 'metric', 'agent_report')", name="ck_feedback_source"),
        sa.CheckConstraint("feedback_type IN ('positive', 'negative', 'neutral', 'metric')", name="ck_feedback_type"),
    )
    op.create_index("idx_feedback_network", "feedback", ["network_id"])

    # Activity Log
    op.create_table(
        "activity_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("network_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("network.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
        sa.Column("detail", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint(
            "event_type IN ('training_step', 'research', 'evaluation', "
            "'output_generated', 'feedback_received', 'weight_adjusted', 'error')",
            name="ck_activity_event_type",
        ),
    )
    op.create_index("idx_activity_network", "activity_log", ["network_id"])
    op.create_index("idx_activity_created", "activity_log", ["network_id", "created_at"])


def downgrade() -> None:
    op.drop_table("activity_log")
    op.drop_table("feedback")
    op.drop_table("generated_output")
    op.drop_table("output_template")
    op.drop_table("evaluation")
    op.drop_table("training_run")
    op.drop_table("component")
    op.drop_table("network")
    op.drop_table("company_brain")
    op.drop_table("company")
