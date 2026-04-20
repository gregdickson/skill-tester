import asyncio
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.models.network import Network
from app.models.component import Component
from app.models.training import TrainingRun
from app.schemas.training import TrainingStartRequest, TrainingRunOut, LossHistoryOut
from app.services.evaluator import Evaluator
from app.services.generator import Generator
from app.services.research_agent import ResearchAgent
from app.services.training_engine import TrainingEngine, get_active_task, set_active_task
from app.routers.websocket import broadcast

router = APIRouter()


@router.post("/{network_id}/train/start", response_model=TrainingRunOut)
async def start_training(
    network_id: UUID,
    body: TrainingStartRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    network = await db.get(Network, network_id)
    if not network:
        raise HTTPException(404, "Network not found")

    # Check for active training
    existing_task = get_active_task(str(network_id))
    if existing_task and not existing_task.done():
        raise HTTPException(409, "Training already in progress")

    components = (
        await db.execute(
            select(Component)
            .where(Component.network_id == network_id)
            .order_by(Component.sort_order)
        )
    ).scalars().all()

    if not components:
        raise HTTPException(400, "No components — generate a plan first")

    # Get next version number
    max_version = await db.execute(
        select(func.max(TrainingRun.version)).where(TrainingRun.network_id == network_id)
    )
    version = (max_version.scalar() or 0) + 1

    run = TrainingRun(
        network_id=network_id,
        version=version,
        config_snapshot=network.network_config or {},
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    # Build services
    llm = request.app.state.openrouter
    evaluator = Evaluator(llm)
    generator = Generator(llm)
    research = ResearchAgent(llm, request.app.state.brave)

    engine = TrainingEngine(
        network=network,
        components=list(components),
        evaluator=evaluator,
        generator=generator,
        research_agent=research,
        db_factory=async_session,
        ws_broadcast=broadcast,
    )

    # Run training in background
    async def train_wrapper():
        try:
            await engine.run_training(run, body.steps)
        finally:
            set_active_task(str(network_id), None)

    task = asyncio.create_task(train_wrapper())
    set_active_task(str(network_id), task)

    return run


@router.post("/{network_id}/train/pause")
async def pause_training(network_id: UUID):
    task = get_active_task(str(network_id))
    if not task or task.done():
        raise HTTPException(404, "No active training")
    # The engine checks _paused flag — we need a reference to the engine
    # For now, cancel the task
    task.cancel()
    set_active_task(str(network_id), None)
    return {"status": "paused"}


@router.post("/{network_id}/train/resume", response_model=TrainingRunOut)
async def resume_training(
    network_id: UUID,
    body: TrainingStartRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Resume is essentially starting a new run from current weights
    return await start_training(network_id, body, request, db)


@router.get("/{network_id}/training-runs", response_model=list[TrainingRunOut])
async def list_training_runs(network_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TrainingRun)
        .where(TrainingRun.network_id == network_id)
        .order_by(TrainingRun.started_at.desc())
    )
    return result.scalars().all()


@router.get("/{network_id}/loss-history", response_model=LossHistoryOut)
async def get_loss_history(network_id: UUID, db: AsyncSession = Depends(get_db)):
    network = await db.get(Network, network_id)
    if not network:
        raise HTTPException(404, "Network not found")

    # Aggregate loss history from all runs
    runs = (
        await db.execute(
            select(TrainingRun)
            .where(TrainingRun.network_id == network_id)
            .order_by(TrainingRun.started_at)
        )
    ).scalars().all()

    combined = []
    offset = 0
    for run in runs:
        for entry in (run.loss_history or []):
            combined.append({"step": entry["step"] + offset, "loss": entry["loss"]})
        offset += run.total_steps

    return LossHistoryOut(
        loss_history=combined,
        current_loss=network.current_loss,
        total_steps=network.total_steps,
    )
