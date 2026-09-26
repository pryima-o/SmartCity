from app.database import SessionLocal
from app.vector_store import DocumentChunk
from app.llm_service import get_embedding

MIN_SIMILARITY = 0.50


def retrieve_relevant_chunks(
    user_query: str,
    limit: int = 3
) -> list:

    query_vector = get_embedding(user_query)

    if not query_vector:
        return []

    db = SessionLocal()

    try:

        results = (
            db.query(DocumentChunk)
            .order_by(
                DocumentChunk.embedding.cosine_distance(
                    query_vector
                )
            )
            .limit(limit)
            .all()
        )

        chunks_data = []

        for chunk in results:

            distance = (
                DocumentChunk.embedding
                .cosine_distance(query_vector)
            )

            # Для надёжности считаем similarity
            # отдельно через Python.
            import math

            a = query_vector
            b = chunk.embedding

            dot = sum(x * y for x, y in zip(a, b))

            norm_a = math.sqrt(
                sum(x * x for x in a)
            )

            norm_b = math.sqrt(
                sum(x * x for x in b)
            )

            similarity = 0.0

            if norm_a > 0 and norm_b > 0:
                similarity = dot / (norm_a * norm_b)

            if similarity < MIN_SIMILARITY:
                continue

            chunks_data.append({
                "text": chunk.text,
                "source_file": chunk.source_file,
                "passage_id": chunk.passage_id,
                "language": chunk.language,
                "similarity": similarity
            })

        return chunks_data

    except Exception as e:

        print(
            f"Ошибка при векторном поиске: {e}"
        )

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