"""日志工具 - 同时输出到控制台和持久化到 SQLite"""
import logging
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from db.models import OperationLog


# 控制台日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("inspire")


async def log_operation(
    db: AsyncSession,
    module: str,
    action: str,
    detail: str = "",
    level: str = "INFO",
):
    """记录操作日志到数据库"""
    log_entry = OperationLog(
        level=level,
        module=module,
        action=action,
        detail=detail,
    )
    db.add(log_entry)
    await db.commit()
    logger.log(getattr(logging, level, logging.INFO), f"[{module}] {action}: {detail}")
