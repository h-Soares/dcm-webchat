from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from typing import List
import database.repository as repository
import database.models as models
import chat_utils
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger("chat-service.server")
username_lock = asyncio.Lock() # lock para evitar race condition

@asynccontextmanager
async def lifespan(app: FastAPI):
    models.create_db()
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

connections: List[WebSocket] = []
ws_usernames = {}

# Endpoint para verificar disponibilidade de username antes de tentar conectar via WebSocket
@app.get("/check-username/{username}")
async def check_username(username: str):
    if username.strip() == "":
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    
    if username in ws_usernames.values():
        raise HTTPException(status_code=409, detail="Nome já em uso")
    
    return {"message": "Username is available"} # retorna JSON 200 (OK)

# Endpoint WebSocket
@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    # Double-check para garantir que ninguém pegou o nome no milissegundo entre a verificação e a conexão websocket
    # Protegido pelo lock para evitar condição de corrida
    async with username_lock:
        if username in ws_usernames.values():
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept()
        connections.append(websocket)
        ws_usernames[websocket] = username

    logger.info("%s connected. Total connections: %d", username, len(connections))

    await chat_utils.send_last_messages(websocket)

    # Notifica login e atualiza contador de usuários sem bloquear (ativamento via fire-and-forget)
    asyncio.create_task(asyncio.to_thread(chat_utils.notify_login, username))
    asyncio.create_task(asyncio.to_thread(chat_utils.notify_user_count, len(connections)))
 
    try:
        while True:
            # recebe mensagem, salva no banco e retransmite para todos os usuários conectados
            rcvd_message = await websocket.receive_text()
            rcvd_message = rcvd_message.strip()

            datetime_now = chat_utils.now()
            await asyncio.to_thread(repository.save_message, datetime_now, username, rcvd_message)
            message = f"[{datetime_now.astimezone().strftime('%H:%M:%S')}] {username}: {rcvd_message}"
            logger.info(message)
            await chat_utils.broadcast(ws_usernames, connections, message)
    except WebSocketDisconnect:
        connections.remove(websocket)
        ws_usernames.pop(websocket, None)
        logger.info("%s disconnected. Total connections: %d", username, len(connections))
        asyncio.create_task(asyncio.to_thread(chat_utils.notify_user_count, len(connections)))