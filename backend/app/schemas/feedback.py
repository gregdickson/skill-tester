from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    output_id: UUID | None = None
    source: str = "manual"
    feedback_type: str = "neutral"
    metric_name: str | None = None
    metric_value: float | None = None
    notes: str | None = None


class FeedbackOut(BaseModel):
    id: UUID
    network_id: UUID
    output_id: UUID | None
    source: str
    feedback_type: str
    metric_name: str | None
    metric_value: float | None
    notes: str | None
    processed: bool
    created_at: datetime

    model_config = {"from_attributes": True}
