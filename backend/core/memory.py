"""长短期记忆管理"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from db.models import Message, LongTermMemory, Session
from services.llm import llm
from config import SHORT_TERM_MAX_MESSAGES, LONG_TERM_SUMMARY_THRESHOLD


async def load_short_term_messages(db: AsyncSession, session_id: str) -> list:
    """加载短期记忆（最近 N 条消息）"""
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(SHORT_TERM_MAX_MESSAGES)
    )
    rows = list(reversed(result.scalars().all()))

    messages = []
    for row in rows:
        if row.role == "human":
            messages.append(HumanMessage(content=row.content))
        elif row.role == "ai":
            messages.append(AIMessage(content=row.content))
        elif row.role == "system":
            messages.append(SystemMessage(content=row.content))
    return messages


async def load_long_term_summary(db: AsyncSession, session_id: str) -> str | None:
    """加载长期记忆摘要"""
    result = await db.execute(
        select(LongTermMemory).where(LongTermMemory.session_id == session_id)
    )
    memory = result.scalar_one_or_none()
    return memory.summary if memory and memory.summary else None


async def save_message(db: AsyncSession, session_id: str, role: str, content: str):
    """保存消息到数据库"""
    msg = Message(session_id=session_id, role=role, content=content)
    db.add(msg)
    await db.commit()


async def maybe_update_long_term_memory(db: AsyncSession, session_id: str):
    """检查是否需要更新长期记忆摘要"""
    # 统计消息数
    result = await db.execute(
        select(Message).where(Message.session_id == session_id)
    )
    messages = result.scalars().all()

    if len(messages) < LONG_TERM_SUMMARY_THRESHOLD:
        return

    # 检查是否已有摘要
    result = await db.execute(
        select(LongTermMemory).where(LongTermMemory.session_id == session_id)
    )
    existing = result.scalar_one_or_none()

    # 构建对话文本用于摘要
    conversation = "\n".join(f"{m.role}: {m.content}" for m in messages)
    prev_summary = existing.summary if existing else ""

    prompt = f"""请将以下对话内容总结为简洁的摘要，保留关键信息和用户偏好。
如果有之前的摘要，请在其基础上更新。

之前的摘要：{prev_summary or '无'}

最近的对话：
{conversation[-3000:]}

请输出更新后的摘要（200字以内）："""

    response = await llm.ainvoke([HumanMessage(content=prompt)])

    if existing:
        existing.summary = response.content
    else:
        new_memory = LongTermMemory(session_id=session_id, summary=response.content)
        db.add(new_memory)
    await db.commit()
