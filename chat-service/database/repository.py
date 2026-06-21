from datetime import datetime
from sqlmodel import Session, col, select
from database.models import engine, Message, User
import hashlib

def save_message(timestamp: datetime, username: str, content: str):
    # Persiste uma mensagem no banco SQLite
    message = Message(timestamp=timestamp, username=username, content=content)

    with Session(engine) as session:
        session.add(message)
        session.commit()

def get_latest_messages(limit: int = 100):
    # Retorna as últimas mensagens mais recentes
    with Session(engine) as session:
        statement = (
            select(Message)
            .order_by(col(Message.timestamp).desc())
            .limit(limit)
        )
        return session.exec(statement).all()
    
# Transforma a senha do usuário em hash (SHA-256)
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Salva um novo usuário cadastrado
def create_user(username: str, password_raw: str) -> User:
    user = User(username=username, password_hash=hash_password(password_raw))
    with Session(engine) as session:
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

# Busca um usuário pelo nome
def get_user_by_username(username: str) -> User | None:
    with Session(engine) as session:
        statement = select(User).where(User.username == username)
        return session.exec(statement).first()