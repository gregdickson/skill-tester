import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

# Connected clients keyed by network_id
_connections: dict[str, list[WebSocket]] = {}


async def broadcast(network_id: str, data: dict):
    """Broadcast a message to all WebSocket clients watching a network."""
    clients = _connections.get(network_id, [])
    message = json.dumps(data)
    disconnected = []
    for ws in clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        clients.remove(ws)


@router.websocket("/ws/networks/{network_id}/activity")
async def activity_ws(websocket: WebSocket, network_id: UUID):
    await websocket.accept()
    nid = str(network_id)

    if nid not in _connections:
        _connections[nid] = []
    _connections[nid].append(websocket)

    try:
        while True:
            # Keep connection alive, handle client messages if needed
            data = await websocket.receive_text()
            # Could handle client commands here (e.g., ping/pong)
    except WebSocketDisconnect:
        pass
    finally:
        if nid in _connections:
            _connections[nid] = [ws for ws in _connections[nid] if ws != websocket]
