from app.database import SessionLocal
from app.vector_store import DocumentChunk
from app.llm_service import get_embedding

def retrieve_relevant_chunks(user_query: str, limit: int = 3) -> list:
    """
    Принимает вопрос пользователя, генерирует эмбеддинг
    и находит топ-N релевантных абзацев в PostgreSQL через Docker.
    """
    # 1. Превращаем вопрос в вектор 3072 чисел
    query_vector = get_embedding(user_query)
    if not query_vector:
        return []

    db = SessionLocal()
    try:
        # 2. Делаем векторный запрос. Оператор косинусного сходства pgvector
        results = db.query(DocumentChunk).order_by(
            DocumentChunk.embedding.cosine_distance(query_vector)
        ).limit(limit).all()

        chunks_data = []
        for chunk in results:
            chunks_data.append({
                "text": chunk.text,
                "source_file": chunk.source_file,
                "passage_id": chunk.passage_id,
                "language": chunk.language
            })
        return chunks_data
    except Exception as e:
        print(f"Ошибка при векторном поиске: {e}")
        return []
    finally:
        db.close()

if __name__ == "__main__":
    print("Тестирование векторного поиска в Docker...")
    # Пишем слово, которое точно есть в нашем regulament.txt (например, про разрешение на строительство)
    test_question = "строительство" 
    matches = retrieve_relevant_chunks(test_question, limit=1)
    
    for i, match in enumerate(matches):
        print(f"\n[Топ-{i+1} совпадение из файла {match['source_file']}, пассаж {match['passage_id']}]:")
        print(match['text'])