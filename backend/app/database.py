import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Находим путь к папке backend и загружаем .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# Собираем URL подключения. Драйвер psycopg (бинарный) подхватится автоматически
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# 2. Создаем движок SQLAlchemy
# pool_pre_ping=True автоматически проверяет живое ли соединение перед запросом
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# 3. Создаем фабрику сессий для работы с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Создаем базовый класс для будущих ORM моделей
Base = declarative_base()

def get_db():
    """
    Контекстный менеджер (генератор) для удобной работы с сессиями.
    Идеально подойдет для интеграции с FastAPI (через Depends).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
