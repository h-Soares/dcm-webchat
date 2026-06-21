from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi import HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import jwt
import os

# Configura o caminho para o arquivo .env para carregar a chave do token JWT
DOTENV_PATH = Path(__file__).resolve().with_name(".env")
load_dotenv(dotenv_path=DOTENV_PATH)

# Configurações do token JWT
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError(f"JWT_SECRET_KEY environment variable is required in {DOTENV_PATH}")

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

class RefreshTokenSchema(BaseModel):
    refresh_token: str

# Cria um token JWT com o nome de usuário, tipo de token e tempo de expiração
def create_jwt_token(username: str, token_type: str, expires_time: timedelta) -> str:
    payload = {
        "sub": username,
        "type": token_type,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + expires_time,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

# Cria tokens de autenticação (access e refresh) para o usuário
def create_auth_tokens(username: str) -> dict:
    access_token = create_jwt_token(username, "access", timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = create_jwt_token(username, "refresh", timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }

# Decodifica o token JWT e verifica se é do tipo esperado (access ou refresh)
def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.get("type") != expected_type:
        raise HTTPException(status_code=401, detail="Invalid token type")

    return payload

# Obtém o nome de usuário associado a um token JWT do tipo esperado
def get_username_by_token(token: str, expected_type: str) -> str:
    payload = decode_token(token, expected_type)
    return payload["sub"]

# Extrai o token Bearer do cabeçalho Authorization
def extract_bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    return authorization.removeprefix("Bearer ").strip()