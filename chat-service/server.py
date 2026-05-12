from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from typing import List
import chat_utils

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

connections: List[WebSocket] = []
ws_usernames = {}

@app.get("/check-username/{username}")
async def check_username(username: str):
    if username.strip() == "":
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    
    if username in ws_usernames.values():
        raise HTTPException(status_code=409, detail="Nome já em uso")
    
    return {"message": "Username is available"} # retorna um objeto JSON com o HTTP Status Code 200 (OK)

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    # Double-check: garante que ninguém pegou o nome no milissegundo entre o check e o connect
    if username in ws_usernames.values():
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    connections.append(websocket)
    ws_usernames[websocket] = username

    print(f"{username} connected. Total connections: {len(connections)}")   

    try:
        while True:
            rcvd_message = await websocket.receive_text()
            rcvd_message = rcvd_message.strip()

            message = f"[{chat_utils.now()}] {username}: {rcvd_message}"

            print(message)
            await chat_utils.broadcast(ws_usernames, connections, message)
    except WebSocketDisconnect:
        connections.remove(websocket)
        ws_usernames.pop(websocket, None)
        print(f"{username} disconnected. Total connections: {len(connections)}")