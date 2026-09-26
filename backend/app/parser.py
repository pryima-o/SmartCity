import os
from pathlib import Path
from sqlalchemy.orm import Session
from database import SessionLocal  # Сессию берем из database.py
from vector_store import DocumentChunk  # Модель берем из vector_store.py
from llm_service import get_embedding

def parse_and_index_file(file_path: str, language: str):
    """
    Читает текстовый файл, режет на абзацы, генерирует эмбеддинги
    и сохраняет всё в базу данных PostgreSQL.
    """
    path = Path(file_path)
    if not path.exists():
        print(f"Файл {file_path} не найден.")
        return

    print(f"Начало обработки файла: {path.name} ({language})")
    
    # Читаем текст документа
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Разбиваем текст по абзацам (двойной перенос строки)
    # Очищаем от лишних пробелов и пустых строк
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

    db: Session = SessionLocal()
    
    try:
        for idx, paragraph_text in enumerate(paragraphs):
            # Пропускаем слишком короткие фрагменты (например, одиночные заголовки без контекста)
            if len(paragraph_text) < 20:
                continue
                
            print(f"Обработка пассажа №{idx + 1}/{len(paragraphs)}...")

            # 1. Получаем векторное представление абзаца через Gemini
            embedding_vector = get_embedding(paragraph_text)
            if not embedding_vector:
                continue  # Если API вернуло ошибку, пропускаем чанк

            # 2. Создаем объект для базы данных
            chunk = DocumentChunk(
                source_file=path.name,
                passage_id=idx + 1,      # ID пассажа для будущих цитат
                text=paragraph_text,
                language=language,
                embedding=embedding_vector
            )
            
            db.add(chunk)
        
        # Сохраняем все чанки в базу данных
        db.commit()
        print(f"Успешно загружено {len(paragraphs)} пассажей из файла {path.name} в БД!")

    except Exception as e:
        db.rollback()
        print(f"Ошибка при сохранении в БД: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    # Динамически находим корень бэкенда (на уровень выше, чем app/)
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # Собираем точный абсолютный путь, который сработает и на ПК, и в Docker
    target_file = BASE_DIR / "data" / "chisinau_docs" / "regulament.txt"
    
    parse_and_index_file(str(target_file), language="ro")
