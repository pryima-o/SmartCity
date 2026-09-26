from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.generation_service import answer_citizen_question

app = FastAPI(
    title="Smart City Chisinau AI Municipal Assistant API",
    description="Официальный API ассистента мэрии Кишинева для хакатона",
    version="1.0.0"
)

# НАСТРОЙКА CORS: Позволяет вашему будущему фронтенду делать запросы к бэкенду
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # На хакатоне разрешаем всем, в продакшене тут будет адрес фронтенда
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Описываем структуру входящего запроса от пользователя
class QuestionRequest(BaseModel):
    question: str

# Описываем структуру ответа бэкенда
class AnswerResponse(BaseModel):
    answer: str

@app.get("/")
def read_root():
    return {"status": "working", "message": "Smart City Assistant API is running"}

@app.post("/api/ask", response_model=AnswerResponse)
def ask_assistant(payload: QuestionRequest):
    """
    Эндпоинт для отправки вопросов граждан.
    Принимает JSON вида: {"question": "как получить разрешение на строительство?"}
    """
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Вопрос не может быть пустым")
    
    # Вызываем нашу готовую RAG логику
    ai_answer = answer_citizen_question(payload.question)
    
    return AnswerResponse(answer=ai_answer)