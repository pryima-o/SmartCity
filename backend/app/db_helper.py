import os
from pathlib import Path
from dotenv import load_dotenv
from psycopg import connect

# Загружаем переменные из .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

def auto_create_database():
    # Подключаемся к дефолтной системной базе данных 'postgres'
    print(f"Подключение к серверу PostgreSQL {DB_HOST}:{DB_PORT}...")
    conn = connect(
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        autocommit=True # Важно для создания баз данных
    )
    
    with conn.cursor() as cur:
        # Проверяем, существует ли база данных SmartCity
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (DB_NAME,))
        exists = cur.fetchone()
        
        if not exists:
            print(f"База данных '{DB_NAME}' не найдена. Создаю...")
            # Внимание: имя базы подставляется через f-строку, так как в SQL CREATE DATABASE нельзя использовать плейсхолдеры %s
            cur.execute(f'CREATE DATABASE "{DB_NAME}";')
            print(f"✅ База данных '{DB_NAME}' успешно создана!")
        else:
            print(f"База данных '{DB_NAME}' уже существует.")
            
    conn.close()

if __name__ == "__main__":
    auto_create_database()
