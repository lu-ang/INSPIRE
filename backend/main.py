"""INSPIRE - FastAPI 入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import CORS_ORIGINS
from db.database import init_db
from api.chat import router as chat_router
from api.sessions import router as sessions_router
from api.knowledge import router as knowledge_router
from api.logs import router as logs_router

#装饰器，异步函数 保证执行
@asynccontextmanager
async def lifespan(app: FastAPI):
    """异步上下文管理器，定义自动执行的代码，应用生命周期：启动时初始化数据库"""
    await init_db()
    yield #之前启动时执行，之后关闭时执行


app = FastAPI(title="INSPIRE", version="0.1.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat_router)
app.include_router(sessions_router)
app.include_router(knowledge_router)
app.include_router(logs_router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
