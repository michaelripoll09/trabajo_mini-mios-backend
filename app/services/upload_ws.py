from typing import Dict, Set
from fastapi import WebSocket

# Conexiones WebSocket por lote
connections: Dict[str, Set[WebSocket]] = {}

async def register(lote_id: str, ws: WebSocket) -> None:
    if lote_id not in connections:
        connections[lote_id] = set()
    connections[lote_id].add(ws)

def unregister(lote_id: str, ws: WebSocket) -> None:
    try:
        connections.get(lote_id, set()).discard(ws)
        if not connections.get(lote_id):
            connections.pop(lote_id, None)
    except Exception:
        pass

async def send_progress(lote_id: str, processed: int, total: int) -> None:
    payload = {"event": "progress", "lote_id": lote_id, "processed": processed, "total": total}
    for ws in list(connections.get(lote_id, set())):
        try:
            await ws.send_json(payload)
        except Exception:
            unregister(lote_id, ws)

async def send_complete(lote_id: str) -> None:
    payload = {"event": "complete", "lote_id": lote_id}
    for ws in list(connections.get(lote_id, set())):
        try:
            await ws.send_json(payload)
        except Exception:
            unregister(lote_id, ws)

