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


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# СХЕМЫ КАТЕГОРИЙ
# ============================================================

class CategoryName(BaseModel):
    ru: str
    ro: str
    en: Optional[str] = None


class CategoryResponse(BaseModel):
    id: str
    name: CategoryName
    slug: str

    @field_validator("id", mode="before")
    @classmethod
    def convert_id_to_str(cls, v):
        return str(v)

    class Config:
        from_attributes = True


class CategoryCreate(BaseModel):
    name: CategoryName
    slug: str


class CategoryUpdate(BaseModel):
    name: Optional[CategoryName] = None
    slug: Optional[str] = None


# ============================================================
# СХЕМЫ ЧАТОВ
# ============================================================

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

    @field_validator("categoryId", mode="before")
    @classmethod
    def convert_cat_id_to_str(cls, v):
        return str(v) if v is not None else None

    class Config:
        from_attributes = True


# ============================================================
# СХЕМЫ СООБЩЕНИЙ
# ============================================================

class SourceResponse(BaseModel):
    title: str
    url: str

    class Config:
        from_attributes = True


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

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        if v is not None and v not in ["like", "dislike"]:
            raise ValueError(
                "Тип фидбека должен быть 'like', 'dislike' или null"
            )
        return v


class NewMessageRequest(BaseModel):
    content: str
    silent: Optional[bool] = False


# ============================================================
# ОФИЦИАЛЬНЫЕ САЙТЫ
# ============================================================

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
    "apacanal.md": "https://acc.md",
}

DEFAULT_SOURCE_URL = "https://chisinau.md"


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def read_root():
    return {
        "status": "working",
        "message": "Smart City Assistant API is running"
    }


# ============================================================
# СООБЩЕНИЯ ЧАТА
# ============================================================

@app.get(
    "/v1/chats/{chat_id}/messages",
    response_model=List[MessageResponse]
)
def get_chat_messages(
    chat_id: str,
    db: Session = Depends(get_db)
):
    chat = (
        db.query(ChatSession)
        .filter(ChatSession.id == chat_id)
        .first()
    )

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Сессия чата не найдена"
        )

    messages = (
        db.query(Message)
        .options(joinedload(Message.sources))
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    formatted_messages = []

    for msg in messages:

        msg_sources = []

        if msg.role == "assistant" and msg.sources:

            seen_src = set()

            for src in msg.sources:

                real_url = DOMAINS_URL_MAP.get(
                    src.document.lower(),
                    DEFAULT_SOURCE_URL
                )

                src_key = (
                    src.document.lower(),
                    real_url
                )

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
            "sources": (
                msg_sources
                if msg.role == "assistant"
                else None
            )
        })

    return formatted_messages


# ============================================================
# НОВОЕ СООБЩЕНИЕ
# ============================================================

@app.post(
    "/v1/chats/{chat_id}/messages",
    response_model=MessageResponse
)
def post_new_message(
    chat_id: str,
    payload: NewMessageRequest,
    db: Session = Depends(get_db)
):

    # Проверяем чат

    chat = (
        db.query(ChatSession)
        .filter(ChatSession.id == chat_id)
        .first()
    )

    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Сессия чата не найдена"
        )

    # Проверяем сообщение

    if not payload.content.strip():
        raise HTTPException(
            status_code=400,
            detail="Сообщение не может быть пустым"
        )

    # Сохраняем сообщение пользователя

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

    # ========================================================
    # RAG + GEMINI
    # ========================================================

    try:

        ai_raw_answer = answer_citizen_question(
            user_question=payload.content
        )

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Ошибка AI-движка: {str(e)}"
        )

    # ========================================================
    # ПОИСК ИСТОЧНИКОВ
    #
    # Поддерживаем:
    #
    # [Sursă: chisinau.md, Pasaj: 15]
    #
    # и:
    #
    # [chisinau.md, Pasaj 15]
    #
    # и:
    #
    # [chisinau.md, Пассаж 15]
    # ========================================================

    source_patterns = [
        re.compile(
            r"\[Sursă:\s*([^,\]]+),\s*(?:Пассаж|Pasaj)\s*:?\s*(\d+)\]",
            re.IGNORECASE
        ),
        re.compile(
            r"\[([^,\]]+),\s*(?:Пассаж|Pasaj)\s*:?\s*(\d+)\]",
            re.IGNORECASE
        ),
    ]

    found_sources = re.findall(
    r"\[([^,\]]+),\s*(?:Пассаж|Pasaj)\s*:?\s*(\d+)\]",
    ai_raw_answer,
    re.IGNORECASE
    )

    for pattern in source_patterns:

        for match in pattern.finditer(ai_raw_answer):

            doc_name = match.group(1).strip()
            passage_id = match.group(2).strip()

            source = (doc_name, passage_id)

            if source not in found_sources:
                found_sources.append(source)

    # ========================================================
    # ОБРАБОТКА ССЫЛОК
    # ========================================================

    clean_content = ai_raw_answer

    formatted_sources_list = []

    seen_sources = set()

    for doc_name, passage_id in found_sources:

        domain = doc_name.strip()

        real_url = DOMAINS_URL_MAP.get(
            domain.lower(),
            DEFAULT_SOURCE_URL
        )

        # Технический формат:
        #
        # [Sursă: rtec.md, Pasaj: 45]
        #
        # превращаем в:
        #
        # [rtec.md](https://rtec.md)

        source_marker_regex = re.compile(
            rf"\[Sursă:\s*{re.escape(domain)},\s*"
            rf"(?:Пассаж|Pasaj)\s*:?\s*"
            rf"{re.escape(passage_id)}\]",
            re.IGNORECASE
        )

        clean_content = source_marker_regex.sub(
            f"[{domain}]({real_url})",
            clean_content
        )

        # Также поддерживаем:
        #
        # [rtec.md, Pasaj 45]

        simple_marker_regex = re.compile(
            rf"\[{re.escape(domain)},\s*"
            rf"(?:Пассаж|Pasaj)\s*:?\s*"
            rf"{re.escape(passage_id)}\]",
            re.IGNORECASE
        )

        clean_content = simple_marker_regex.sub(
            f"[{domain}]({real_url})",
            clean_content
        )

        # Источник для frontend

        source_key = (
            domain.lower(),
            passage_id
        )

        if source_key not in seen_sources:

            seen_sources.add(source_key)

            formatted_sources_list.append({
                "title": f"{domain} (Pasaj {passage_id})",
                "url": real_url
            })

    # ========================================================
    # СОХРАНЯЕМ ОТВЕТ ASSISTANT
    # ========================================================

    assistant_msg_id = f"msg_{uuid.uuid4().hex[:6]}"

    assistant_message = Message(
        id=assistant_msg_id,
        chat_id=chat_id,
        role="assistant",
        content=clean_content,
        feedback=None
    )

    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    # ========================================================
    # СОХРАНЯЕМ ИСТОЧНИКИ
    # ========================================================

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

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "id": assistant_message.id,
        "role": assistant_message.role,
        "content": assistant_message.content,
        "feedback": assistant_message.feedback,
        "createdAt": assistant_message.created_at,
        "sources": formatted_sources_list
    }


# ============================================================
# FEEDBACK
# ============================================================

@app.post(
    "/v1/messages/{message_id}/feedback",
    response_model=MessageResponse
)
def set_message_feedback(
    message_id: str,
    payload: FeedbackRequest,
    db: Session = Depends(get_db)
):

    message = (
        db.query(Message)
        .options(joinedload(Message.sources))
        .filter(Message.id == message_id)
        .first()
    )

    if not message:
        raise HTTPException(
            status_code=404,
            detail="Сообщение не найдено"
        )

    if message.role != "assistant":
        raise HTTPException(
            status_code=400,
            detail="Оценивать можно только ответы ассистента"
        )

    message.feedback = payload.type

    db.commit()
    db.refresh(message)

    msg_sources = []

    if message.sources:

        seen_src = set()

        for src in message.sources:

            real_url = DOMAINS_URL_MAP.get(
                src.document.lower(),
                DEFAULT_SOURCE_URL
            )

            src_key = (
                src.document.lower(),
                src.passage
            )

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
        "sources": msg_sources
    }


# ============================================================
# СОЗДАНИЕ ЧАТА
# ============================================================

@app.post(
    "/v1/chats",
    response_model=ChatCreateResponse,
    status_code=status.HTTP_201_CREATED
)
def create_chat_session(
    payload: ChatCreateRequest,
    db: Session = Depends(get_db)
):

    if not payload.query.strip():

        raise HTTPException(
            status_code=400,
            detail="Первый запрос не может быть пустым"
        )

    generated_chat_id = (
        f"chat_{uuid.uuid4().hex[:6]}"
    )

    # Определяем язык

    has_cyrillic = any(
        "\u0400" <= c <= "\u04FF"
        for c in payload.query
    )

    detected_lang = (
        "ru"
        if has_cyrillic
        else "ro"
    )

    # Генерируем title

    words = payload.query.split()

    generated_title = " ".join(words[:4])

    if len(words) > 4:
        generated_title += "..."

    # Создаем ChatSession

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
        db.refresh(new_session)

        # Первое сообщение пользователя

        first_msg = Message(
            id=f"msg_{uuid.uuid4().hex[:6]}",
            chat_id=generated_chat_id,
            role="user",
            content=payload.query
        )

        db.add(first_msg)
        db.commit()

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при создании чата: {str(e)}"
        )

    return ChatCreateResponse(
        id=new_session.id
    )


# ============================================================
# ДЕТАЛИ ЧАТА
# ============================================================

@app.get(
    "/v1/chats/{chat_id}",
    response_model=ChatDetailResponse
)
def get_chat_session_detail(
    chat_id: str,
    db: Session = Depends(get_db)
):

    chat = (
        db.query(ChatSession)
        .filter(ChatSession.id == chat_id)
        .first()
    )

    if not chat:

        raise HTTPException(
            status_code=404,
            detail="Сессия чата не найдена"
        )

    return {
        "id": chat.id,
        "categoryId": chat.category_id,
        "title": chat.title,
        "lang": chat.lang,
        "category": None,
        "createdAt": chat.created_at,
        "updatedAt": chat.updated_at
    }


# ============================================================
# КАТЕГОРИИ
# ============================================================

@app.get(
    "/v1/categories",
    response_model=List[CategoryResponse]
)
def get_categories(
    db: Session = Depends(get_db)
):

    categories = (
        db.query(Category)
        .all()
    )

    return [
        {
            "id": cat.id,
            "name": {
                "ru": cat.name_ru,
                "ro": cat.name_ro,
                "en": cat.name_en
            },
            "slug": cat.slug
        }
        for cat in categories
    ]


@app.post(
    "/v1/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED
)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db)
):

    new_cat = Category(
        name_ru=payload.name.ru,
        name_ro=payload.name.ro,
        name_en=(
            payload.name.en
            if payload.name.en
            else ""
        ),
        slug=payload.slug
    )

    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)

    return {
        "id": new_cat.id,
        "name": {
            "ru": new_cat.name_ru,
            "ro": new_cat.name_ro,
            "en": new_cat.name_en
        },
        "slug": new_cat.slug
    }


@app.delete(
    "/v1/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db)
):

    db_cat = (
        db.query(Category)
        .filter(Category.id == category_id)
        .first()
    )

    if not db_cat:

        raise HTTPException(
            status_code=404,
            detail="Категория не найдена"
        )

    db.delete(db_cat)
    db.commit()

    return None


# ============================================================
# БЮДЖЕТ
# ============================================================

@app.get("/v1/budget")
def get_maintenance_budget():

    monthly_requests = 50_000

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

    # Gemini Flash

    flash_input_cost = (
        total_input_tokens /
        1_000_000
    ) * 0.75

    flash_output_cost = (
        total_output_tokens /
        1_000_000
    ) * 3.75

    flash_total = (
        flash_input_cost +
        flash_output_cost
    )

    # Gemini Flash-Lite

    lite_input_cost = (
        total_input_tokens /
        1_000_000
    ) * 0.25

    lite_output_cost = (
        total_output_tokens /
        1_000_000
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

            "model":
                "Gemini 3.8 Flash",

            "deployment":
                "Google Gemini API",

            "input_cost":
                round(
                    flash_input_cost,
                    2
                ),

            "output_cost":
                round(
                    flash_output_cost,
                    2
                ),

            "embedding_cost":
                embedding_cost,

            "estimated_monthly_ai_cost":
                round(
                    flash_total +
                    embedding_cost,
                    2
                ),

            "frontend": 0,

            "backend": 0,

            "estimated_total":
                round(
                    flash_total +
                    embedding_cost,
                    2
                )
        },

        "cost_optimized": {

            "model":
                "Gemini 3.1 Flash-Lite",

            "input_cost":
                round(
                    lite_input_cost,
                    2
                ),

            "output_cost":
                round(
                    lite_output_cost,
                    2
                ),

            "embedding_cost":
                embedding_cost,

            "estimated_monthly_ai_cost":
                round(
                    lite_total +
                    embedding_cost,
                    2
                ),

            "frontend": 0,

            "backend": 0,

            "estimated_total":
                round(
                    lite_total +
                    embedding_cost,
                    2
                )
        },

        "self_hosted": {

            "model":
                "Llama 3.x class model",

            "deployment":
                "EU/Moldova data center",

            "gpu_server": 350,

            "database": 40,

            "estimated_total": 390
        }
    }