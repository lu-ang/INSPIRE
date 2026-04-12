"""INSPIRE 项目配置"""
import os
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent

# 数据存储目录
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
CHROMA_DIR = DATA_DIR / "chroma"
CHROMA_DIR.mkdir(exist_ok=True)

# SQLite 数据库
DATABASE_URL = f"sqlite+aiosqlite:///{DATA_DIR / 'inspire.db'}"

# LLM 配置（阿里百炼 OpenAI 兼容接口）
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "qwen-max")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")

# RAG 配置
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
RAG_TOP_K = 5

# 记忆配置
SHORT_TERM_MAX_MESSAGES = 20  # 短期记忆最大消息数
LONG_TERM_SUMMARY_THRESHOLD = 10  # 触发长期摘要的消息数阈值

# CORS
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
