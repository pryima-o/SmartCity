from google import genai
from google.genai import types
from app.search_service import retrieve_relevant_chunks


client = genai.Client(http_options={"api_version": "v1"})


MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.1-flash-lite",
]


def answer_citizen_question(user_question: str) -> str:

    # ==========================================================
    # 1. RAG SEARCH
    # ==========================================================

    context_chunks = retrieve_relevant_chunks(
        user_query=user_question,
        limit=3
    )

    if not context_chunks:
        return (
            "Данной информации нет в официальных документах.\n\n"
            "Официальный сайт: chisinau.md"
        )

    # ==========================================================
    # 2. CONTEXT
    # ==========================================================

    formatted_context = ""

    for chunk in context_chunks:
        formatted_context += (
            f"[DOCUMENT: {chunk['source_file']}]\n"
            f"[PASSAGE: {chunk['passage_id']}]\n"
            f"[SIMILARITY: {chunk['similarity']:.3f}]\n"
            f"{chunk['text']}\n\n"
        )

    # ==========================================================
    # 3. SYSTEM INSTRUCTION
    # ==========================================================

    system_instruction = """
Ты — официальный AI-ассистент муниципалитета Кишинева.

Твоя задача — отвечать гражданам исключительно на основании
предоставленного КОНТЕКСТА из официальных документов.

ПРАВИЛА:

1. Отвечай на языке вопроса:
   - русский → русский
   - румынский → румынский

2. НИКОГДА не используй знания вне КОНТЕКСТА.

3. Если в контексте нет достаточной информации для ответа,
   прямо скажи:

   "Данной информации нет в официальных документах."

4. Если два или более документа содержат противоречащие
   друг другу сведения, НЕ выбирай один из них самостоятельно.

   Вместо этого укажи:

   "В официальных документах обнаружено противоречие."

   После этого кратко укажи оба варианта и их источники.

5. Для каждого существенного утверждения указывай источник
   в формате:

   [document.md, Пассаж X]

6. Используй ТОЛЬКО document и passage из КОНТЕКСТА.

7. Не выдумывай:
   - документы
   - пассажи
   - URL
   - даты
   - суммы
   - адреса
   - правила

8. Отвечай кратко и непосредственно.
   Не повторяй вопрос пользователя.

9. Не используй Markdown-ссылки.

10. В конце ответа НЕ добавляй отдельный список ссылок.
    Источники будут добавлены системой автоматически.
"""

    prompt = f"""
КОНТЕКСТ:

{formatted_context}

ВОПРОС ГРАЖДАНИНА:

{user_question}
"""

    # ==========================================================
    # 4. GENERATION
    # ==========================================================

    for model_name in MODELS:

        try:

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,

                    # Ключевая оптимизация latency/cost
                    thinking_config=types.ThinkingConfig(
                        thinking_level="low"
                    ),

                    # Ограничиваем длину ответа
                    max_output_tokens=500,
                ),
            )

            answer = response.text

            if answer and answer.strip():
                return answer.strip()

        except Exception as e:

            error = str(e).lower()

            print(
                f"⚠️ Gemini {model_name} failed: {e}"
            )

            # При rate limit / overload сразу идём
            # к следующей модели.
            if (
                "503" in error
                or "429" in error
                or "resource_exhausted" in error
                or "overloaded" in error
                or "demand" in error
            ):
                continue

            # Любая другая ошибка модели тоже
            # не должна ломать весь запрос.
            continue

    return (
        "Сервис AI временно недоступен.\n"
        "Пожалуйста, повторите запрос через несколько секунд."
    )