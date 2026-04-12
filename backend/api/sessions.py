"""会话管理 API"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import Session as SessionModel, Message
from utils.logger import log_operation

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    title: str = "新对话"
    knowledge_base_id: str | None = None


class UpdateSessionRequest(BaseModel):
    title: str | None = None
    knowledge_base_id: str | None = None


@router.get("")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """获取所有会话列表"""
    result = await db.execute(
        select(SessionModel).order_by(SessionModel.updated_at.desc())
    )
    sessions = result.scalars().all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "knowledge_base_id": s.knowledge_base_id,
            "created_at": s.created_at.isoformat(),
            "updated_at": s.updated_at.isoformat(),
        }
        for s in sessions
    ]


@router.post("")
async def create_session(req: CreateSessionRequest, db: AsyncSession = Depends(get_db)):
    """创建新会话"""
    session = SessionModel(title=req.title, knowledge_base_id=req.knowledge_base_id)
    db.add(session)
    await db.commit()
    await db.refresh(session)
    await log_operation(db, "chat", "create_session", f"id={session.id}, title={req.title}")
    return {"id": session.id, "title": session.title}


@router.get("/{session_id}/messages")
async def get_session_messages(session_id: str, db: AsyncSession = Depends(get_db)):
    """获取会话的所有消息"""
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


@router.put("/{session_id}")
async def update_session(session_id: str, req: UpdateSessionRequest, db: AsyncSession = Depends(get_db)):
    """更新会话信息"""
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "会话不存在"}
    if req.title is not None:
        session.title = req.title
    if req.knowledge_base_id is not None:
        session.knowledge_base_id = req.knowledge_base_id
    await db.commit()
    return {"id": session.id, "title": session.title}


@router.delete("/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """删除会话"""
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        return {"error": "会话不存在"}
    await db.delete(session)
    await db.commit()
    await log_operation(db, "chat", "delete_session", f"id={session_id}")
    return {"ok": True}
