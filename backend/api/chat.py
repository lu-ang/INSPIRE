"""对话 API"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import get_db
from db.models import Session as SessionModel
from core.agent import chat_stream
from utils.logger import log_operation

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    session_id: str
    message: str


@router.post("/stream")
async def chat_stream_api(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    """流式对话接口"""
    # 查询会话获取关联的知识库
    result = await db.execute(
        select(SessionModel).where(SessionModel.id == req.session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "会话不存在"}

    kb_id = session.knowledge_base_id

    await log_operation(db, "chat", "send_message", f"session={req.session_id}, kb={kb_id}")

    async def event_generator():
        async for chunk in chat_stream(db, req.session_id, req.message, kb_id):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
