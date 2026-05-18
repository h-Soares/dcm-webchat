from datetime import datetime, timezone
from fastapi import WebSocket
from typing import List
import asyncio
import grpc
import notification_pb2
import notification_pb2_grpc
from database.repository import get_latest_messages
import logging

logger = logging.getLogger("chat-service.chat_utils")

def now() -> datetime:
    # Retorna timestamp em UTC
    return datetime.now(timezone.utc)

async def send_safe(ws: WebSocket, text: str) -> bool:
    # Envia texto para o WebSocket; retorna False se falhar (ex.: conexão fechada)
    try:
        await ws.send_text(text)
        return True
    except Exception:
        return False

async def broadcast(ws_usernames: dict, connections: List[WebSocket], text: str) -> None:
    # Envia mensagem para todas as conexões; remove as que falham
    for ws in list(connections):
        if not await send_safe(ws, text):
            connections.remove(ws)
            ws_usernames.pop(ws, None)

async def send_last_messages(websocket: WebSocket):
    # Recupera as últimas mensagens do banco e envia ao cliente que conectou
    messages = await asyncio.to_thread(get_latest_messages)
    for message in reversed(messages):
        message_text = f"[{message.timestamp.replace(tzinfo=timezone.utc).astimezone().strftime('%H:%M:%S')}] {message.username}: {message.content}"
        await send_safe(websocket, message_text)

def notify_login(username: str, host: str = "localhost:9090") -> None:
    try:
        # Chama função gRPC para o notification-service notificar o login para todos os usuários
        logger.info("[gRPC] Notifying login for user: %s", username)
        with grpc.insecure_channel(host) as channel:
            stub = notification_pb2_grpc.NotificationServiceStub(channel)
            response = stub.NotifyLogin(notification_pb2.NotifyRequest(username=username))  # type: ignore
            logger.info("[gRPC] Login notified successfully for %s: %s", username, response.status)
    except Exception as e:
        logger.exception("[gRPC] Unexpected error notifying login for %s: %s", username, e)


def notify_user_count(user_count: int, host: str = "localhost:9090") -> None:
    try:
        # Chama função gRPC para o notification-service notificar o número de usuários conectados para todos os usuários
        logger.info("[gRPC] Notifying user count: %d", user_count)
        with grpc.insecure_channel(host) as channel:
            stub = notification_pb2_grpc.NotificationServiceStub(channel)
            response = stub.NotifyUserCount(notification_pb2.NotifyCountRequest(user_count=user_count))  # type: ignore
            logger.info("[gRPC] User count notified successfully: %s", response.status)
    except Exception as e:
        logger.exception("[gRPC] Unexpected error notifying user count: %s", e)