from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class NetworkCreate(BaseModel):
    company_id: UUID
    title: str
    purpose: str | None = None
    ultimate_end_goal: str
    how_it_works: str | None = None
    network_config: dict = {}
    reference_files: list = []


class NetworkUpdate(BaseModel):
    title: str | None = None
    purpose: str | None = None
    ultimate_end_goal: str | None = None
    status: str | None = None
    mode: str | None = None
    how_it_works: str | None = None
    network_config: dict | None = None
    learning_config: dict | None = None
    command_config: dict | None = None
    reference_files: list | None = None


class NetworkOut(BaseModel):
    id: UUID
    company_id: UUID
    title: str
    purpose: str | None
    ultimate_end_goal: str
    status: str
    mode: str
    readiness_pct: float
    current_loss: float | None
    total_steps: int
    network_config: dict
    how_it_works: str | None
    reference_files: list
    learning_config: dict
    command_config: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NetworkConfigOut(BaseModel):
    config: dict

    model_config = {"from_attributes": True}


class GeneratePlanRequest(BaseModel):
    research_depth: int = 3
