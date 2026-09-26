import os
import re
import time
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import SessionLocal  
from app.vector_store import DocumentChunk  
from app.llm_service import get_embedding

def parse_and_index_file(file_path: str):
    """
    Читает текстовый файл, нарезает его строго по разделительным линиям из дефисов,
    вытаскивает метаданные пассажа, определяет язык и заливает векторы в pgvector.
    Включена максимальная защита от поминутных лимитов Google API (TPM/RPM 429).
    """
    path = Path(file_path)
    if not path.exists():
        print(f"Файл {file_path} не найден.")
        return

    print(f"🚀 Начало умной обработки файла: {path.name}")
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Нарезаем текст строго по линиям из дефисов, разделяющим пассажи
    raw_passages = [p.strip() for p in content.split("------------------------------------------------------------------------------------------") if p.strip()]

    db: Session = SessionLocal()
    uploaded_count = 0
    
    try:
        for idx, passage_text in enumerate(raw_passages):
            # Пропускаем вводные заголовки документа (шапки категорий и ANNEX)
            if "ANNEX 1" in passage_text or ("CATEGORIE:" in passage_text and "[PASAJ" not in passage_text):
                continue

            # Вычищаем техническую шапку пассажа строго по румынским маркерам
            clean_text = re.sub(r"\[PASAJ\s*#\d+\].*", "", passage_text, flags=re.IGNORECASE)
            clean_text = re.sub(r"Categorie\s*:\s*[^\n]+", "", clean_text, flags=re.IGNORECASE)
            clean_text = re.sub(r"Sursă\s*\(domeniu\)\s*:\s*[^\n]+", "", clean_text, flags=re.IGNORECASE)
            clean_text = re.sub(r"URL\s*:\s*[^\n]+", "", clean_text, flags=re.IGNORECASE)
            clean_text = clean_text.strip()

            # Если после очистки остался пустой текст — пропускаем
            if len(clean_text) < 15:
                continue

            # Вытаскиваем реальный номер пассажа из текста (например, из "[PASAJ #158]")
            passage_id_match = re.search(r"\[PASAJ\s*#(\d+)\]", passage_text, re.IGNORECASE)
            actual_passage_id = int(passage_id_match.group(1)) if passage_id_match else (idx + 1)

            # Вытаскиваем реальный домен ведомства (например, liftservice.md)
            source_match = re.search(r"Sursă\s*\(domeniu\)\s*:\s*([^\n]+)", passage_text, re.IGNORECASE)
            source_file_name = source_match.group(1).strip() if source_match else path.name

            # Умное определение языка пассажа (наличие кириллицы -> ru, иначе -> ro)
            has_cyrillic = any(u'\u0400' <= c <= u'\u04FF' for c in clean_text)
            detected_lang = "ru" if has_cyrillic else "ro"
                
            print(f"⏳ Индексация пассажа №{actual_passage_id} ({detected_lang}) для {source_file_name}...")

            # --- БРОНЕБОЙНАЯ ЗАЩИТА ОТ RATE LIMITS ---
            embedding_vector = None
            max_retries = 5  # До 5 попыток со сном
            
            for retry in range(max_retries):
                try:
                    embedding_vector = get_embedding(clean_text)
                    if embedding_vector:
                        break  # Успешно получили вектор, выходим из цикла ретраев
                except Exception as api_err:
                    error_str = str(api_err)
                    # Если поймали ограничение квот Google, засыпаем надолго
                    if "429" in error_str or "exhausted" in error_str.lower():
                        wait_time = (retry + 1) * 15  # 15 сек, затем 30 сек, затем 45 сек
                        print(f"🛑 Превышена поминутная квота знаков Google (429). Ждем {wait_time} сек...")
                        time.sleep(wait_time)
                    else:
                        print(f"⚠️ Ошибка API на пассаже №{actual_passage_id}: {api_err}")
                        time.sleep(2)

            if not embedding_vector:
                print(f"❌ Критическая ошибка: пассаж №{actual_passage_id} пропущен после {max_retries} попыток.")
                continue  

            # Сохраняем объект в pgvector таблицу
            chunk = DocumentChunk(
                source_file=source_file_name,  # Передаем домен (например chisinau.md) для инлайн-цитат фронтенда!
                passage_id=actual_passage_id,      
                text=clean_text,
                language=detected_lang,
                embedding=embedding_vector
            )
            
            db.add(chunk)
            uploaded_count += 1
            
            # Базовая задержка между пассажами, чтобы не раздражать API
            time.sleep(2.5)
        
        # Фиксируем транзакцию в PostgreSQL
        db.commit()
        print(f"\n✅ УСПЕХ! Проиндексировано и загружено {uploaded_count} чанков в векторную базу данных!")

    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при сохранении в БД: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    # Находим абсолютный путь к файлу базы знаний
    BASE_DIR = Path(__file__).resolve().parent.parent
    target_file = BASE_DIR / "data" / "chisinau_docs" / "regulament.txt"
    
    parse_and_index_file(str(target_file))
