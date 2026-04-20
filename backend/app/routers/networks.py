import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.network import Network
from app.models.component import Component
from app.schemas.network import NetworkCreate, NetworkUpdate, NetworkOut, GeneratePlanRequest
from app.schemas.component import ComponentOut
from app.services.research_agent import ResearchAgent

router = APIRouter()


@router.get("", response_model=list[NetworkOut])
async def list_networks(company_id: UUID | None = None, db: AsyncSession = Depends(get_db)):
    query = select(Network).order_by(Network.created_at.desc())
    if company_id:
        query = query.where(Network.company_id == company_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=NetworkOut, status_code=201)
async def create_network(body: NetworkCreate, db: AsyncSession = Depends(get_db)):
    network = Network(**body.model_dump())
    db.add(network)
    await db.commit()
    await db.refresh(network)
    return network


@router.get("/{network_id}", response_model=NetworkOut)
async def get_network(network_id: UUID, db: AsyncSession = Depends(get_db)):
    network = await db.get(Network, network_id)
    if not network:
        raise HTTPException(404, "Network not found")
    return network


@router.put("/{network_id}", response_model=NetworkOut)
async def update_network(network_id: UUID, body: NetworkUpdate, db: AsyncSession = Depends(get_db)):
    network = await db.get(Network, network_id)
    if not network:
        raise HTTPException(404, "Network not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(network, key, value)
    await db.commit()
    await db.refresh(network)
    return network


@router.post("/{network_id}/generate-plan", response_model=list[ComponentOut])
async def generate_plan(
    network_id: UUID,
    body: GeneratePlanRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    network = await db.get(Network, network_id)
    if not network:
        raise HTTPException(404, "Network not found")

    agent = ResearchAgent(request.app.state.openrouter, request.app.state.brave)
    raw_components = await agent.decompose_into_components(
        goal=network.ultimate_end_goal,
        title=network.title,
        purpose=network.purpose,
        research_depth=body.research_depth,
    )

    # Clear existing components
    existing = await db.execute(
        select(Component).where(Component.network_id == network_id)
    )
    for c in existing.scalars().all():
        await db.delete(c)

    # Create new components
    created = []
    for i, raw in enumerate(raw_components):
        comp = Component(
            network_id=network_id,
            name=raw.get("name", f"Component {i+1}"),
            description=raw.get("description", ""),
            priority=raw.get("priority", "medium"),
            weight=raw.get("initial_weight", 0.5),
            initial_weight=raw.get("initial_weight", 0.5),
            sort_order=i,
            sub_components=raw.get("sub_components", []),
            research_notes=raw.get("rationale", ""),
        )
        db.add(comp)
        created.append(comp)

    await db.commit()
    for c in created:
        await db.refresh(c)
    return created


@router.get("/{network_id}/config/{mode}")
async def get_config(network_id: UUID, mode: str, db: AsyncSession = Depends(get_db)):
    network = await db.get(Network, network_id)
    if not network:
        raise HTTPException(404, "Network not found")
    config = network.learning_config if mode == "learn" else network.command_config
    return {"config": config, "how_it_works": network.how_it_works, "network_config": network.network_config}


@router.put("/{network_id}/config/{mode}")
async def update_config(network_id: UUID, mode: str, body: dict, db: AsyncSession = Depends(get_db)):
    network = await db.get(Network, network_id)
    if not network:
        raise HTTPException(404, "Network not found")

    if "how_it_works" in body:
        network.how_it_works = body.pop("how_it_works")
    if "network_config" in body:
        network.network_config = {**(network.network_config or {}), **body.pop("network_config")}

    config_field = "learning_config" if mode == "learn" else "command_config"
    current = getattr(network, config_field) or {}
    setattr(network, config_field, {**current, **body})

    await db.commit()
    return {"status": "updated"}
