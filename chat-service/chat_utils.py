from datetime import datetime, timezone
from fastapi import WebSocket
from typing import List
import asyncio
import grpc
import notification_pb2
import notification_pb2_grpc
import database.repository as repository
import logging

logger = logging.getLogger("chat-service.chat_utils")

# Retorna timestamp em UTC
def now() -> datetime:
    return datetime.now(timezone.utc)

# Envia texto para a conexão WebSocket. Retorna False se falhar (ex.: conexão fechada)
async def send_safe(ws: WebSocket, text: str) -> bool:
    try:
        await ws.send_text(text)
        return True
    except Exception:
        return False

# Envia mensagem para todas as conexões; remove as que falham
async def broadcast(ws_usernames: dict, connections: List[WebSocket], text: str) -> None:
    for ws in list(connections):
        if not await send_safe(ws, text):
            connections.remove(ws)
            ws_usernames.pop(ws, None)

# Recupera as últimas mensagens do banco e as envia para a conexão WebSocket
async def send_last_messages(websocket: WebSocket):
    messages = await asyncio.to_thread(repository.get_latest_messages)
    for message in reversed(messages):
        message_text = f"[{message.timestamp.replace(tzinfo=timezone.utc).astimezone().strftime('%H:%M:%S')}] {message.username}: {message.content}"
        await send_safe(websocket, message_text)

# Atua como cliente gRPC: chama função gRPC para o notification-service notificar o login para todos os usuários
def notify_login(username: str, host: str = "localhost:9090") -> None:
    try:
        logger.info("[gRPC] Notifying login for user: %s", username)
        with grpc.insecure_channel(host) as channel:
            stub = notification_pb2_grpc.NotificationServiceStub(channel)
            response = stub.NotifyLogin(notification_pb2.NotifyRequest(username=username))  # type: ignore
            logger.info("[gRPC] Login notified successfully for %s: %s", username, response.status)
    except Exception as e:
        logger.exception("[gRPC] Unexpected error notifying login for %s: %s", username, e)

# Atua como cliente gRPC: chama função gRPC para o notification-service notificar o número de usuários conectados para todos os usuários
def notify_user_count(user_count: int, host: str = "localhost:9090") -> None:
    try:
        logger.info("[gRPC] Notifying user count: %d", user_count)
        with grpc.insecure_channel(host) as channel:
            stub = notification_pb2_grpc.NotificationServiceStub(channel)
            response = stub.NotifyUserCount(notification_pb2.NotifyCountRequest(user_count=user_count))  # type: ignore
            logger.info("[gRPC] User count notified successfully: %s", response.status)
    except Exception as e:
        logger.exception("[gRPC] Unexpected error notifying user count: %s", e)