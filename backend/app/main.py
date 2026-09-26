from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from typing import List, Optional
from sqlalchemy.orm import Session

from app.database import get_db
from app.vector_store import Category
from app.generation_service import answer_citizen_question

app = FastAPI(
    title="Smart City Chisinau AI Municipal Assistant API",
    description="Официальный API ассистента мэрии Кишинева для хакатона",
    version="1.0.0"
)

# НАСТРОЙКА CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ОБНОВЛЕННЫЕ СХЕМЫ ВАЛИДАЦИИ (Pydantic) ---

class QuestionRequest(BaseModel):
    question: str

class AnswerResponse(BaseModel):
    answer: str

class CategoryName(BaseModel):
    ru: str
    ro: str
    en: str

# Схема ответа (GET) — превращает интовый ID из базы в строку для фронтендера
class CategoryResponse(BaseModel):
    id: str  # Оставляем String для фронтендера
    name: CategoryName
    slug: str

    @field_validator('id', mode='before')
    @classmethod
    def convert_id_to_str(cls, v):
        return str(v)  # Автоматически переводит 1 -> "1"

    class Config:
        from_attributes = True

# Схема создания (POST) — ТЕПЕРЬ ТУТ НЕТ ПОЛЯ ID! Фронтенд его больше не шлет.
class CategoryCreate(BaseModel):
    name: CategoryName
    slug: str

# Схема обновления (PATCH)
class CategoryUpdate(BaseModel):
    name: Optional[CategoryName] = None
    slug: Optional[str] = None


# --- ЭНДПОИНТЫ API ---

@app.get("/")
def read_root():
    return {"status": "working", "message": "Smart City Assistant API is running"}


# 1. GET /v1/categories — Получение всех категорий
@app.get("/v1/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    result = []
    for cat in categories:
        result.append({
            "id": cat.id,  # Передаем число, Pydantic сам сделает из него строку
            "name": {"ru": cat.name_ru, "ro": cat.name_ro, "en": cat.name_en},
            "slug": cat.slug
        })
    return result


# 2. POST /v1/categories — Создание новой категории (ID генерируется сам)
@app.post("/v1/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    # Проверяем уникальность слага
    db_cat_exists = db.query(Category).filter(Category.slug == payload.slug).first()
    if db_cat_exists:
        raise HTTPException(status_code=400, detail="Категория с таким slug уже существует")

    new_cat = Category(
        name_ru=payload.name.ru,
        name_ro=payload.name.ro,
        name_en=payload.name.en,
        slug=payload.slug
    )
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat) # База сама присвоит ему порядковый ID (например, 1)
    
    return {
        "id": new_cat.id,
        "name": {"ru": new_cat.name_ru, "ro": new_cat.name_ro, "en": new_cat.name_en},
        "slug": new_cat.slug
    }


# 3. PATCH /v1/categories/{id} — Частичное обновление категории
@app.patch("/v1/categories/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)):
    db_cat = db.query(Category).filter(Category.id == category_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    if payload.slug is not None:
        db_cat.slug = payload.slug
    if payload.name is not None:
        db_cat.name_ru = payload.name.ru
        db_cat.name_ro = payload.name.ro
        db_cat.name_en = payload.name.en

    db.commit()
    db.refresh(db_cat)

    return {
        "id": db_cat.id,
        "name": {"ru": db_cat.name_ru, "ro": db_cat.name_ro, "en": db_cat.name_en},
        "slug": db_cat.slug
    }


# 4. DELETE /v1/categories/{id} — Удаление категории
@app.delete("/v1/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    db_cat = db.query(Category).filter(Category.id == category_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    
    db.delete(db_cat)
    db.commit()
    return None
