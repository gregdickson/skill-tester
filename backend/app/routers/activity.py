from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.activity import ActivityLog

router = APIRouter()


@router.get("/{network_id}/activity")
async def list_activity(
    network_id: UUID,
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    event_type: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(ActivityLog)
        .where(ActivityLog.network_id == network_id)
        .order_by(ActivityLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    if event_type:
        query = query.where(ActivityLog.event_type == event_type)
    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        {
            "id": str(log.id),
            "event_type": log.event_type,
            "message": log.message,
            "detail": log.detail,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
