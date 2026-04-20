from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()


@router.post("/{network_id}/chat", response_model=ChatResponse)
async def chat(
    network_id: UUID,
    body: ChatRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    service = ChatService(request.app.state.openrouter)
    result = await service.handle_message(network_id, body.mode, body.message, db)
    await db.commit()
    return ChatResponse(**result)
