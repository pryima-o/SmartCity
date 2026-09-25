import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai

# Подгружаем API-ключ из .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Инициализируем официальный клиент Google. 
# Он автоматически подтянет ключ GEMINI_API_KEY из вашего .env
client = genai.Client()

def get_embedding(text: str) -> list[float]:
    """
    Превращает текст в вектор с помощью официального Gemini SDK.
    """
    try:
        safe_text = text.encode('utf-8', errors='ignore').decode('utf-8')
        
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=safe_text
        )
        
        # ИСПРАВЛЕНИЕ: Берем первый элемент из списка эмбеддингов и забираем его значения
        return response.embeddings[0].values
    except Exception as e:
        print(f"Ошибка при генерации эмбеддинга через SDK: {e}")
        return []

# Тест для проверки
if __name__ == "__main__":
    print("Проверка официального Gemini SDK с вашим ключом...")
    vector = get_embedding("Primăria Municipiului Chișinău — тест")
    if vector:
        print(f"✅ Успех! Получен вектор. Размерность: {len(vector)}")
        print(f"Первые 3 числа вектора: {vector[:3]}")
    else:
        print("❌ Не удалось получить вектор. Проверьте правильность GEMINI_API_KEY в .env")
