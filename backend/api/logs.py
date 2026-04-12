"""日志查询 API"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import OperationLog

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("")
async def list_logs(
    module: str | None = Query(None, description="按模块筛选: chat/knowledge/system"),
    level: str | None = Query(None, description="按级别筛选: INFO/WARN/ERROR"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """查询操作日志"""
    query = select(OperationLog)
    if module:
        query = query.where(OperationLog.module == module)
    if level:
        query = query.where(OperationLog.level == level)
    query = query.order_by(desc(OperationLog.created_at)).offset(offset).limit(limit)

    result = await db.execute(query)
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "level": log.level,
            "module": log.module,
            "action": log.action,
            "detail": log.detail,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]
