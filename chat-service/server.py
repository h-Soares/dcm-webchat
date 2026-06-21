from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, status, Query, Header
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from auth import RefreshTokenSchema, create_auth_tokens, extract_bearer_token, get_username_by_token
from typing import List
from pydantic import BaseModel
import asyncio
import database.repository as repository
import database.models as models
import chat_utils
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
logger = logging.getLogger("chat-service.server")

class UserAuthSchema(BaseModel):
    username: str
    password: str

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
    allow_headers=["*"],
)

connections: List[WebSocket] = []
ws_usernames = {}

# Rota para cadastro de novos usuários
@app.post("/register")
def register(user_input: UserAuthSchema):
    username = user_input.username.strip()
    password = user_input.password.strip()

    if not username or not password:
        raise HTTPException(status_code=400, detail="Campos não podem ser vazios")

    existing_user = repository.get_user_by_username(username)
    if existing_user:
        raise HTTPException(status_code=409, detail="Nome de usuário já está em uso")

    repository.create_user(username, password)
    return {"message": "Usuário cadastrado com sucesso!"}

# Rota para login com retorno de token JWT
@app.post("/login")
def login(user_input: UserAuthSchema):
    user = repository.get_user_by_username(user_input.username.strip())
    if not user or repository.hash_password(user_input.password.strip()) != user.password_hash:
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")

    return create_auth_tokens(user.username)

# Rota para obter novos tokens usando o refresh token
@app.post("/refresh")
def refresh_tokens(user_input: RefreshTokenSchema):
    username = get_username_by_token(user_input.refresh_token.strip(), "refresh")
    return create_auth_tokens(username)

# Rota para validar e obter informações do usuário utilizando o access token
@app.get("/me")
def me(authorization: str | None = Header(default=None)):
    token = extract_bearer_token(authorization)
    username = get_username_by_token(token, "access")
    return {"username": username}

# Endpoint WebSocket que recebe o access token via query string para autenticar o usuário automaticamente
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    try:
        username = get_username_by_token(token, "access")
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    connections.append(websocket)
    ws_usernames[websocket] = username

    total_unique_users = len(set(ws_usernames.values()))
    logger.info("%s connected. Online users: %d", username, total_unique_users)

    await chat_utils.send_last_messages(websocket)

    # Notifica login e atualiza contador de usuários sem bloquear (ativamento via fire-and-forget)
    asyncio.create_task(asyncio.to_thread(chat_utils.notify_login, username))
    asyncio.create_task(asyncio.to_thread(chat_utils.notify_user_count, total_unique_users))

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
        total_unique_users = len(set(ws_usernames.values()))
        logger.info("%s disconnected. Online users: %d", username, total_unique_users)
        asyncio.create_task(asyncio.to_thread(chat_utils.notify_user_count, total_unique_users))