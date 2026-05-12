from datetime import datetime
from fastapi import WebSocket
from typing import List

def now() -> str:
    return datetime.now().strftime("%H:%M:%S")

async def send_safe(ws: WebSocket, text: str) -> bool:
    try:
        await ws.send_text(text)
        return True
    except Exception:
        return False

async def broadcast(ws_usernames: dict, connections: List[WebSocket], text: str) -> None:
    disconnected = []
    for ws in list(connections):
        ok = await send_safe(ws, text)
        if not ok:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in connections:
            connections.remove(ws)
            ws_usernames.pop(ws, None)