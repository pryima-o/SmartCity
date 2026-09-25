from sqlalchemy import Column, Integer, String, Text, text  # Добавили импорт text
from pgvector.sqlalchemy import Vector
from database import Base, engine

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    source_file = Column(String, nullable=False)
    passage_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    language = Column(String(5), nullable=False)
    
    # Размерность 3072 под модель gemini-embedding-001
    embedding = Column(Vector(3072)) 

def init_db():
    """
    Включает pgvector и создает таблицы в базе данных.
    """
    with engine.connect() as conn:
        # ИСПРАВЛЕНИЕ: Обернули текстовый запрос в функцию text()
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()  # Явно сохраняем подключение расширения
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Пересоздание/Инициализация структуры таблиц...")
    init_db()
    print("✅ Таблицы успешно созданы в БД SmartCity!")