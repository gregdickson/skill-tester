from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ComponentCreate(BaseModel):
    name: str
    description: str | None = None
    priority: str = "medium"
    weight: float = 0.5
    sort_order: int = 0
    sub_components: list = []


class ComponentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    priority: str | None = None
    weight: float | None = None
    score_pct: float | None = None
    status: str | None = None
    sort_order: int | None = None
    sub_components: list | None = None
    research_notes: str | None = None


class ComponentOut(BaseModel):
    id: UUID
    network_id: UUID
    name: str
    description: str | None
    priority: str
    weight: float
    initial_weight: float
    score_pct: float
    status: str
    sort_order: int
    sub_components: list
    research_notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReorderRequest(BaseModel):
    ids: list[UUID]
