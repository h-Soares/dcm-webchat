from datetime import datetime
from sqlmodel import SQLModel, Field, create_engine
from pathlib import Path

# Colocar o arquivo SQLite dentro da pasta "database" como chat.db e configurar o banco de de dados com ORM usando SQLModel.
DB_PATH = Path(__file__).resolve().parent / "chat.db"
DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False}
)

class Message(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    timestamp: datetime
    username: str
    content: str

def create_db():
    SQLModel.metadata.create_all(engine)