"""LLM 配置"""
from langchain_openai import ChatOpenAI
from config import LLM_BASE_URL, LLM_MODEL

llm = ChatOpenAI(
    model=LLM_MODEL,
    base_url=LLM_BASE_URL,
    streaming=True,
)
