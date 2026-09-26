from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
import uuid
import re


from app.database import get_db
from app.vector_store import Category, ChatSession, Message, MessageSource
from app.generation_service import answer_citizen_question

app = FastAPI(
    title="Smart City Chisinau AI Municipal Assistant API",
    description="Официальный API ассистента мэрии Кишинева для хакатона",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- СХЕМЫ ВАЛИДАЦИИ КАТЕГОРИЙ ---
class CategoryName(BaseModel):
    ru: str
    ro: str
    en: Optional[str] = None

class CategoryResponse(BaseModel):
    id: str  
    name: CategoryName
    slug: str
    @field_validator('id', mode='before')
    @classmethod
    def convert_id_to_str(cls, v): return str(v)
    class Config: from_attributes = True

class CategoryCreate(BaseModel):
    name: CategoryName
    slug: str

class CategoryUpdate(BaseModel):
    name: Optional[CategoryName] = None
    slug: Optional[str] = None

# --- СХЕМЫ ВАЛИДАЦИИ ЧАТОВ ---
class ChatCreateRequest(BaseModel):
    query: str
    categoryId: Optional[str] = None

class ChatCreateResponse(BaseModel):
    id: str

class ChatDetailResponse(BaseModel):
    id: str
    categoryId: Optional[str] = None
    title: str
    lang: str
    category: Optional[CategoryResponse] = None
    createdAt: datetime
    updatedAt: datetime
    @field_validator('categoryId', mode='before')
    @classmethod
    def convert_cat_id_to_str(cls, v): return str(v) if v is not None else None
    class Config: from_attributes = True

# --- СХЕМЫ ВАЛИДАЦИИ СООБЩЕНИЙ ---
# ИСПРАВЛЕНИЕ: Теперь отдаем строго title и url по запросу фронтенда
class SourceResponse(BaseModel):
    title: str
    url: str
    class Config: from_attributes = True

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    feedback: Optional[str] = None 
    createdAt: datetime
    sources: Optional[List[SourceResponse]] = None

    class Config:
        from_attributes = True


class FeedbackRequest(BaseModel):
    type: Optional[str] = None 
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v is not None and v not in ["like", "dislike"]:
            raise ValueError("Тип фидбека должен быть 'like', 'dislike' или null")
        return v

class NewMessageRequest(BaseModel):
    content: str
    silent: Optional[bool] = False # НОВОЕ ПОЛЕ: если true, бэкенд не дублирует сообщение юзера в базу

# Карта официальных сайтов ведомств мэрии из Annex 1 для генерации URL
DOMAINS_URL_MAP = {
    "chisinau.md": "https://chisinau.md",
    "rtec.md": "https://rtec.md",
    "autourban.md": "http://autourban.md",
    "dgaurf.md": "https://dgaurf.md",
    "proiecte.chisinau.md": "https://chisinau.md",
    "botanica.md": "https://preturabotanica.md",
    "ciocana.md": "https://preturaciocana.md",
    "centru.md": "https://preturacentru.md",
    "buiucani.md": "https://preturabuiucani.md",
    "riscani.md": "https://preturariscani.md",
    "help.chisinau.md": "https://chisinau.md",
    "extrupo.md": "http://exdrupo.md",
    "liftservice.md": "http://liftservice.md",
    "infocom.md": "https://infocom.md",
    "imi.md": "https://imi.md",
    "apacanal.md": "https://acc.md"
}


# --- ЭНДПОИНТЫ API ---

@app.get("/")
def read_root():
    return {"status": "working", "message": "Smart City Assistant API is running"}


# ==========================================
#       РУЧКИ ДЛЯ СООБЩЕНИЙ В ЧАТЕ
# ==========================================

@app.get("/v1/chats/{chat_id}/messages", response_model=List[MessageResponse])
def get_chat_messages(chat_id: str, db: Session = Depends(get_db)):
    chat = db.query(ChatSession).filter(ChatSession.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Сессия чата не найдена")

    messages = db.query(Message).options(joinedload(Message.sources)).filter(Message.chat_id == chat_id).order_by(Message.created_at.asc()).all()
    
    formatted_messages = []
    for msg in messages:
        # Собираем источники в новом формате
        msg_sources = []
        if msg.role == "assistant" and msg.sources:
            seen_src = set()
            for src in msg.sources:
                real_url = DOMAINS_URL_MAP.get(src.document.lower(), "https://chisinau.md")
                src_key = (src.document, real_url)
                if src_key not in seen_src:
                    seen_src.add(src_key)
                    msg_sources.append({
                        "title": f"{src.document} ({src.passage})",
                        "url": real_url
                    })

        formatted_messages.append({
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "feedback": msg.feedback,
            "createdAt": msg.created_at,
            "sources": msg_sources if msg.role == "assistant" else None
        })
    return formatted_messages



@app.post("/v1/chats/{chat_id}/messages", response_model=MessageResponse)
def post_new_message(chat_id: str, payload: NewMessageRequest, db: Session = Depends(get_db)):
    chat = db.query(ChatSession).filter(ChatSession.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Сессия чата не найдена")

    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")

    # 1. Сохраняем сообщение пользователя
    if not payload.silent:
        user_msg_id = f"msg_{uuid.uuid4().hex[:6]}"
        user_message = Message(id=user_msg_id, chat_id=chat_id, role="user", content=payload.content)
        db.add(user_message)
        db.commit()

    # 2. Вызываем движок Gemini
    # 2. Получаем историю текущего чата
    # 1. Получаем историю ДО сохранения текущего сообщения
    history_messages = (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    chat_history = [
        {
            "role": msg.role,
            "content": msg.content
        }
        for msg in history_messages
    ]

    # 2. Сохраняем сообщение пользователя
    if not payload.silent:
        user_msg_id = f"msg_{uuid.uuid4().hex[:6]}"

        user_message = Message(
            id=user_msg_id,
            chat_id=chat_id,
            role="user",
            content=payload.content
        )

        db.add(user_message)
        db.commit()

    # 3. Gemini получает историю + текущий вопрос
    ai_raw_answer = answer_citizen_question(
        user_question=payload.content,
        chat_history=chat_history
    )

    # 3. Ищем регуляркой цитаты вида [домен.md, Pasaj: X]
    found_sources = re.findall(r"\[([^,]+),\s*(?:Пассаж|Pasaj)\s*:?\s*(\d+)\]", ai_raw_answer, re.IGNORECASE)

    # 4. УМНАЯ ЛОГИКА: Превращаем текстовые цитаты в тексте в Markdown ссылки [chisinau.md](https://chisinau.md)
    # И заменяем pasaj/пассаж на красивый вид для гражданина
    clean_content = ai_raw_answer
    formatted_sources_list = []
    seen_sources = set() # Чтобы не дублировать одинаковые ссылки в массиве sources

    for doc_name, passage_id in found_sources:
        domain = doc_name.strip()
        # Вычисляем красивую ссылку из нашей карты (или оставляем базовый chisinau.md, если домена нет в списке)
        real_url = DOMAINS_URL_MAP.get(domain.lower(), f"https://chisinau.md")
        
        # Делаем замену в тексте ответа ИИ: [rtec.md, Pasaj: 45] -> [rtec.md](https://rtec.md)
        raw_marker_regex = rf"\[{re.escape(doc_name)},\s*(?:Пассаж|Pasaj)\s*:?\s*{passage_id}\]"
        clean_content = re.sub(raw_marker_regex, f"[{domain}]({real_url})", clean_content, flags=re.IGNORECASE)

        # Собираем данные для массива sources для фронтендера
        source_key = (domain, real_url)
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            formatted_sources_list.append({
                "title": f"{domain} (Pasaj {passage_id})",
                "url": real_url
            })

    # 5. Сохраняем ответ ассистента в PostgreSQL
    assistant_msg_id = f"msg_{uuid.uuid4().hex[:6]}"
    assistant_message = Message(id=assistant_msg_id, chat_id=chat_id, role="assistant", content=clean_content, feedback=None)
    db.add(assistant_message)
    db.commit()

    # 6. Сохраняем источники в техническую таблицу SQL
    for doc_name, passage_id in found_sources:
        domain = doc_name.strip()
        new_source = MessageSource(
            message_id=assistant_msg_id,
            document=domain,
            passage=f"Pasaj {passage_id}"
        )
        db.add(new_source)
    if found_sources:
        db.commit()

    return {
        "id": assistant_message.id,
        "role": "assistant",
        "content": assistant_message.content,
        "feedback": assistant_message.feedback,
        "createdAt": assistant_message.created_at,
        "sources": formatted_sources_list # Возвращаем строго title и url!
    }


# 3. POST /v1/messages/{message_id}/feedback — Бонусная система лайков/дизлайков
@app.post("/v1/messages/{message_id}/feedback", response_model=MessageResponse)
def set_message_feedback(message_id: str, payload: FeedbackRequest, db: Session = Depends(get_db)):
    message = db.query(Message).options(joinedload(Message.sources)).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    if message.role != "assistant":
        raise HTTPException(status_code=400, detail="Оценивать можно только ответы ассистента")

    message.feedback = payload.type
    db.commit()
    db.refresh(message)

    # Приводим источники к единому формату фронтенда (title + url)
    msg_sources = []
    if message.sources:
        seen_src = set()
        for src in message.sources:
            real_url = DOMAINS_URL_MAP.get(src.document.lower(), "https://chisinau.md")
            src_key = (src.document, real_url)
            if src_key not in seen_src:
                seen_src.add(src_key)
                msg_sources.append({
                    "title": f"{src.document} ({src.passage})",
                    "url": real_url
                })

    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "feedback": message.feedback,
        "createdAt": message.created_at,
        "sources": msg_sources  # Теперь фронтенд отработает без ошибок валидации!
    }


# ==========================================
#         РУЧКИ ДЛЯ СЕССИЙ ЧАТОВ
# ==========================================

# 1. POST /v1/chats — Создание чата

@app.post("/v1/chats", response_model=ChatCreateResponse, status_code=status.HTTP_201_CREATED)
def create_chat_session(payload: ChatCreateRequest, db: Session = Depends(get_db)):
    if not payload.query.strip(): 
        raise HTTPException(status_code=400, detail="Первый запрос не может быть пустым")
        
    generated_chat_id = f"chat_{uuid.uuid4().hex[:6]}"
    has_cyrillic = any(u'\u0400' <= c <= u'\u04FF' for c in payload.query)
    detected_lang = "ru" if has_cyrillic else "ro"
    words = payload.query.split()
    generated_title = " ".join(words[:4]) + ("..." if len(words) > 4 else "")

    new_session = ChatSession(
        id=generated_chat_id, 
        category_id=payload.categoryId, 
        title=generated_title, 
        lang=detected_lang, 
        first_query=payload.query
    )
    
    try:
        db.add(new_session)
        db.commit()
        
        first_msg = Message(id=f"msg_{uuid.uuid4().hex[:6]}", chat_id=generated_chat_id, role="user", content=payload.query)
        db.add(first_msg)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при создании чата: {e}")
    
    return ChatCreateResponse(id=new_session.id)



# 2. GET /v1/chats/{chat_id} — Детали чата
@app.get("/v1/chats/{chat_id}", response_model=ChatDetailResponse)
def get_chat_session_detail(chat_id: str, db: Session = Depends(get_db)):
    chat = db.query(ChatSession).filter(ChatSession.id == chat_id).first()
    if not chat: 
        raise HTTPException(status_code=404, detail="Сессия чата не найдена")
    
    return {
        "id": chat.id, 
        "categoryId": chat.category_id, 
        "title": chat.title, 
        "lang": chat.lang, 
        "category": None, 
        "createdAt": chat.created_at, 
        "updatedAt": chat.updated_at
    }


# ==========================================
#          РУЧКИ ДЛЯ КАТЕГОРИЙ (CRUD)
# ==========================================

@app.get("/v1/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    return [{"id": cat.id, "name": {"ru": cat.name_ru, "ro": cat.name_ro, "en": cat.name_en}, "slug": cat.slug} for cat in categories]


@app.post("/v1/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    new_cat = Category(name_ru=payload.name.ru, name_ro=payload.name.ro, name_en=payload.name.en if payload.name.en else "", slug=payload.slug)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return {"id": new_cat.id, "name": {"ru": new_cat.name_ru, "ro": new_cat.name_ro, "en": new_cat.name_en}, "slug": new_cat.slug}

@app.delete("/v1/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    db_cat = db.query(Category).filter(Category.id == category_id).first()
    if not db_cat: 
        raise HTTPException(status_code=404, detail="Категория не найдена")
    db.delete(db_cat)
    db.commit()
    return None


# ==========================================
#              РУЧКА БЮДЖЕТА
# ==========================================

@app.get("/v1/budget")
def get_maintenance_budget():

    monthly_requests = 50_000

    # Estimated average usage per request
    input_tokens_per_request = 1200
    output_tokens_per_request = 250

    total_input_tokens = (
        monthly_requests *
        input_tokens_per_request
    )

    total_output_tokens = (
        monthly_requests *
        output_tokens_per_request
    )

    # Gemini 3.8 Flash pricing through Dec 31, 2026
    flash_input_cost = (
        total_input_tokens / 1_000_000
    ) * 0.75

    flash_output_cost = (
        total_output_tokens / 1_000_000
    ) * 3.75

    flash_total = (
        flash_input_cost +
        flash_output_cost
    )

    # Gemini 3.1 Flash-Lite
    lite_input_cost = (
        total_input_tokens / 1_000_000
    ) * 0.25

    lite_output_cost = (
        total_output_tokens / 1_000_000
    ) * 1.50

    lite_total = (
        lite_input_cost +
        lite_output_cost
    )

    embedding_cost = 1.0

    return {
        "currency": "USD",
        "monthly_requests": monthly_requests,

        "usage_assumptions": {
            "input_tokens_per_request":
                input_tokens_per_request,
            "output_tokens_per_request":
                output_tokens_per_request
        },

        "external_api": {
            "model": "Gemini 3.8 Flash",
            "deployment": "Google Gemini API",
            "input_cost": round(
                flash_input_cost, 2
            ),
            "output_cost": round(
                flash_output_cost, 2
            ),
            "embedding_cost": embedding_cost,
            "estimated_monthly_ai_cost": round(
                flash_total + embedding_cost, 2
            ),
            "frontend": 0,
            "backend": 0,
            "estimated_total": round(
                flash_total + embedding_cost, 2
            )
        },

        "cost_optimized": {
            "model": "Gemini 3.1 Flash-Lite",
            "input_cost": round(
                lite_input_cost, 2
            ),
            "output_cost": round(
                lite_output_cost, 2
            ),
            "embedding_cost": embedding_cost,
            "estimated_monthly_ai_cost": round(
                lite_total + embedding_cost, 2
            ),
            "frontend": 0,
            "backend": 0,
            "estimated_total": round(
                lite_total + embedding_cost, 2
            )
        },

        "self_hosted": {
            "model": "Llama 3.x class model",
            "deployment": "EU/Moldova data center",
            "gpu_server": 350,
            "database": 40,
            "estimated_total": 390
        }
    }
