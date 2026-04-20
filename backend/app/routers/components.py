from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.component import Component
from app.schemas.component import ComponentCreate, ComponentUpdate, ComponentOut, ReorderRequest

router = APIRouter()


@router.get("/{network_id}/components", response_model=list[ComponentOut])
async def list_components(network_id: UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Component)
        .where(Component.network_id == network_id)
        .order_by(Component.sort_order)
    )
    return result.scalars().all()


@router.post("/{network_id}/components", response_model=ComponentOut, status_code=201)
async def create_component(network_id: UUID, body: ComponentCreate, db: AsyncSession = Depends(get_db)):
    comp = Component(network_id=network_id, initial_weight=body.weight, **body.model_dump())
    db.add(comp)
    await db.commit()
    await db.refresh(comp)
    return comp


@router.put("/{network_id}/components/{component_id}", response_model=ComponentOut)
async def update_component(
    network_id: UUID, component_id: UUID, body: ComponentUpdate, db: AsyncSession = Depends(get_db)
):
    comp = await db.get(Component, component_id)
    if not comp or comp.network_id != network_id:
        raise HTTPException(404, "Component not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(comp, key, value)
    await db.commit()
    await db.refresh(comp)
    return comp


@router.post("/{network_id}/components/reorder")
async def reorder_components(network_id: UUID, body: ReorderRequest, db: AsyncSession = Depends(get_db)):
    for i, comp_id in enumerate(body.ids):
        await db.execute(
            update(Component)
            .where(Component.id == comp_id, Component.network_id == network_id)
            .values(sort_order=i)
        )
    await db.commit()
    return {"status": "reordered"}
