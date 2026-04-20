from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class OutputTemplateCreate(BaseModel):
    network_id: UUID | None = None
    name: str
    output_type: str = "skill_md"
    master_rule: str | None = None
    prompt_template: str | None = None
    format_rules: dict = {}


class OutputTemplateUpdate(BaseModel):
    name: str | None = None
    output_type: str | None = None
    master_rule: str | None = None
    prompt_template: str | None = None
    format_rules: dict | None = None


class OutputTemplateOut(BaseModel):
    id: UUID
    network_id: UUID | None
    name: str
    output_type: str
    master_rule: str | None
    prompt_template: str | None
    format_rules: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GenerateOutputRequest(BaseModel):
    template_id: UUID | None = None


class GeneratedOutputOut(BaseModel):
    id: UUID
    network_id: UUID
    template_id: UUID | None
    version: int
    content: str
    weights_snapshot: dict
    quality_score: float | None
    human_score: float | None
    pushed_to: str | None
    pushed_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
