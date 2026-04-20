from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    paperclip_config: dict = {}


class CompanyUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    paperclip_config: dict | None = None


class CompanyOut(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    paperclip_config: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CompanyBrainOut(BaseModel):
    id: UUID
    company_id: UUID
    knowledge_base: dict
    cross_references: dict
    last_synthesis: datetime | None
    updated_at: datetime

    model_config = {"from_attributes": True}
