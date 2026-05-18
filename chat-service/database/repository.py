from datetime import datetime
from sqlmodel import Session, col, select
from database.models import engine, Message

def save_message(timestamp: datetime, username: str, content: str):
    # Persiste uma mensagem no banco SQLite
    message = Message(
        timestamp=timestamp,
        username=username,
        content=content
    )

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