from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from pgvector.sqlalchemy import Vector
from app.database import Base, engine

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True, index=True)
    source_file = Column(String, nullable=False)
    passage_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    language = Column(String(5), nullable=False)
    embedding = Column(Vector(3072)) 

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name_ru = Column(String, nullable=False)
    name_ro = Column(String, nullable=False)
    name_en = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, index=True)
    category_id = Column(String, nullable=True)  # Принимает "trab3728" напрямую
    title = Column(String, nullable=False, default="Conversație nouă")
    lang = Column(String(5), nullable=False, default="ro")
    first_query = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Связь с сообщениями восстановлена
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    chat_id = Column(String, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(10), nullable=False)
    content = Column(Text, nullable=False)
    feedback = Column(String(10), nullable=True) 
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    chat = relationship("ChatSession", back_populates="messages")
    sources = relationship("MessageSource", back_populates="message", cascade="all, delete-orphan")

class MessageSource(Base):
    __tablename__ = "message_sources"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    message_id = Column(String, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    document = Column(String, nullable=False)
    passage = Column(Text, nullable=False)

    message = relationship("Message", back_populates="sources")

def init_db():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Пересоздание/Инициализация структуры таблиц...")
    init_db()
    print("✅ Таблицы успешно созданы в БД SmartCity!")
