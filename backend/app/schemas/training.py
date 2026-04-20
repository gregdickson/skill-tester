from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class TrainingStartRequest(BaseModel):
    steps: int = 50


class TrainingRunOut(BaseModel):
    id: UUID
    network_id: UUID
    version: int
    status: str
    total_steps: int
    loss_start: float | None
    loss_end: float | None
    loss_history: list
    improvements: dict
    config_snapshot: dict
    started_at: datetime
    completed_at: datetime | None
    duration_seconds: int | None

    model_config = {"from_attributes": True}


class EvaluationOut(BaseModel):
    id: UUID
    training_run_id: UUID
    component_id: UUID
    step_number: int
    nudge_direction: str
    nudge_delta: float | None
    score_before: float | None
    score_after: float | None
    evaluator_notes: str | None
    research_performed: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class LossHistoryOut(BaseModel):
    loss_history: list[dict]
    current_loss: float | None
    total_steps: int
