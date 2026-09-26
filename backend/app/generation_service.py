import os
from google import genai
from google.genai import types
from app.search_service import retrieve_relevant_chunks
# Инициализируем клиента Gemini для работы с текстовой моделью
client = genai.Client()

def answer_citizen_question(user_question: str) -> str:
    """
    Полный RAG-цикл: ищет контекст в БД и генерирует строгий ответ через Gemini Flash.
    """
    # 1. Извлекаем топ-3 релевантных пассажа из нашей базы данных PostgreSQL
    context_chunks = retrieve_relevant_chunks(user_query=user_question, limit=3)
    
    if not context_chunks:
        return "Îmi pare rău, nu am găsit documente relevante. / К сожалению, релевантных документов не найдено."

    # 2. Форматируем контекст для ИИ с указанием метаданных для цитирования
    formatted_context = ""
    for chunk in context_chunks:
        formatted_context += f"[Sursă: {chunk['source_file']}, Pasaj: {chunk['passage_id']}]\nТекст: {chunk['text']}\n\n"

    # 3. Жесткий системный промпт, полностью закрывающий критерии жюри хакатона
    system_instruction = (
        "Ты — официальный ИИ-ассистент мэрии Кишинева (Primăria Municipiului Chișinău).\n"
        "Твоя задача — отвечать на вопросы граждан строго на основе предоставленного Контекста.\n"
        "ПРАВИЛА:\n"
        "1. Отвечай на том языке, на котором задан вопрос (Romanian или Russian).\n"
        "2. Для каждого утверждения в ответе ОБЯЗАТЕЛЬНО указывай источник в формате [Название документа, Пассаж X] в конце предложения.\n"
        "3. Если в Контексте нет прямого ответа на вопрос, или если документов недостаточно, прямо ответь: "
        "'Данной информации нет в официальных документах' и автоматически предложи обратиться на сайт chisinau.md.\n"
        "4. Если документы противоречат друг другу, четко укажи на это противоречие.\n"
        "Строго запрещено выдумывать факты, которых нет в предоставленном тексте."
    )

    # Собираем промпт
    prompt = f"КОНТЕКСТ ИЗ ОФИЦИАЛЬНЫХ ДОКУМЕНТОВ мэрии:\n{formatted_context}\n\nВОПРОС ГРАЖДАНИНА: {user_question}"

    try:
        # Используем быструю и дешевую модель gemini-1.5-flash
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,  # Нулевая температура полностью убирает креативность и исключает галлюцинации
            ),
        )
        return response.text
    except Exception as e:
        return f"Eroare la generarea răspunsului: {e}"

if __name__ == "__main__":
    print("🤖 Тестирование полноценной RAG-системы Smart City...")
    
    # Тест 1: Вопрос на русском языке
    print("\n--- ТЕСТ 1 (Русский запрос) ---")
    q1 = "Как мне получить разрешение на строительство и сколько дней это займет?"
    print(f"Вопрос: {q1}")
    print(f"Ответ ИИ:\n{answer_citizen_question(q1)}")
    
    # Тест 2: Вопрос на румынском языке
    print("\n--- ТЕСТ 2 (Румынский запрос) ---")
    q2 = "Cum pot solicita audiențe online la primărie?"
    print(f"Вопрос: {q2}")
    print(f"Ответ ИИ:\n{answer_citizen_question(q2)}")

    # Тест 3: Проверка защиты от галлюцинаций (Вопрос, на который нет ответа в базе)
    print("\n--- ТЕСТ 3 (Проверка галлюцинаций) ---")
    q3 = "Какая стоимость проезда в троллейбусе Кишинева?"
    print(f"Вопрос: {q3}")
    print(f"Ответ ИИ:\n{answer_citizen_question(q3)}")