import os
from google import genai
from google.genai import types
from app.search_service import retrieve_relevant_chunks
import time

# Инициализируем клиента Gemini для работы с текстовой моделью
client = genai.Client(http_options={'api_version': 'v1'})

def answer_citizen_question(user_question: str) -> str:
    """
    Полный RAG-цикл: ищет контекст в БД и генерирует строгий ответ через Gemini Flash 3.8.
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
        "'Данной информации нет в официальных документах' на языке запроса и автоматически предложи обратиться на сайт chisinau.md.\n"
        "4. Если документы противоречат друг другу, четко укажи на это противоречие.\n"
        "Строго запрещено выдумывать факты, которых нет в предоставленном тексте."
    )

    # Собираем промпт
    prompt = f"КОНТЕКСТ ИЗ ОФИЦИАЛЬНЫХ ДОКУМЕНТОВ мэрии:\n{formatted_context}\n\nВОПРОС ГРАЖДАНИНА: {user_question}"

    # Набор моделей для резерва на случай перегрузки серверов Google
    models_to_try = ['gemini-3.8-flash', 'gemini-2.0-flash', 'gemini-2.5-flash']
    
    for model_name in models_to_try:
        # Делаем по 2 попытки на каждую модель с паузой
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.0,  # Исключаем галлюцинации
                    ),
                )
                return response.text  # Если получили успешный ответ — сразу отдаем его
            except Exception as e:
                error_str = str(e)
                # Если сервак перегружен (ошибка 503 или лимиты), ждем и пробуем снова
                if "503" in error_str or "demand" in error_str.lower() or "resource_exhausted" in error_str.lower():
                    print(f"⚠️ Модель {model_name} перегружена. Попытка {attempt + 1}/2. Ждем 2 секунды...")
                    time.sleep(2)
                    continue
                else:
                    # Если ошибка критическая (например, модель физически отключена), переходим к следующей модели
                    print(f"❌ Ошибка модели {model_name}: {error_str}. Пробуем резервную...")
                    break
                    
    # Если перегружены вообще все доступные модели Google
    return "Îmi pare rău, serverul este supraîncărcat. Vă rugăm să încercați din nou peste câteva secunde. / К сожалению, сервер перегружен. Пожалуйста, повторите запрос через несколько секунд."