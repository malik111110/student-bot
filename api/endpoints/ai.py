from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict

from core.llm import chat_completion


router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    model: str | None = None
    max_tokens: int = 512


@router.post("/chat")
async def chat(req: ChatRequest):
    result = await chat_completion(
        messages=[m.model_dump() for m in req.messages],
        model=req.model,
        max_tokens=req.max_tokens,
    )
    return {"reply": result}


