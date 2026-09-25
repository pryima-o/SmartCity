import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector


load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    source_file = Column(String, nullable=False)  # Имя файла (например, "regulament_2025.pdf")
    passage_id = Column(Integer, nullable=False)   # Порядковый номер абзаца для цитирования
    text = Column(Text, nullable=False)            # Сам текст абзаца (на румынском или русском)
    language = Column(String(5), nullable=False)   # "ro" или "ru"
    
    # Векторное представление текста. 
    # Размерность 768 используется, если выберете текстовые эмбеддинги от Google Gemini (text-embedding-004)
    embedding = Column(Vector(768)) 

def init_db():
    # Перед созданием таблиц нужно убедиться, что расширение pgvector включено в Postgres
    with engine.connect() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    Base.metadata.create_all(bind=engine)


