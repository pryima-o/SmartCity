from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()


class Question(BaseModel):
    question: str
    language: str


@app.get("/")
def root():
    return {"message": "Smart City API is running"}


@app.post("/chat")
def chat(data: Question):
    return {
        "answer": f"Получен вопрос: {data.question}",
        "language": data.language
    }