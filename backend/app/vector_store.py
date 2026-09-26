from sqlalchemy import Column, Integer, String, Text, text
from pgvector.sqlalchemy import Vector
from app.database import Base, engine

# Существующая модель DocumentChunk (оставляем без изменений)
class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True, index=True)
    source_file = Column(String, nullable=False)
    passage_id = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    language = Column(String(5), nullable=False)
    embedding = Column(Vector(3072)) 

# НОВАЯ МОДЕЛЬ: Таблица для категорий
class Category(Base):
    __tablename__ = "categories"

    # Теперь PostgreSQL будет сам увеличивать ID при каждой записи (1, 2, 3...)
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name_ru = Column(String, nullable=False)
    name_ro = Column(String, nullable=False)
    name_en = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)

def init_db():
    """
    Включает pgvector и создает таблицы в базе данных.
    """
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Пересоздание/Инициализация структуры таблиц...")
    init_db()
    print("✅ Таблицы успешно созданы в БД SmartCity!")
