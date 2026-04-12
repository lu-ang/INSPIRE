"""Embedding 服务"""
from langchain_openai import OpenAIEmbeddings
from config import LLM_BASE_URL, EMBEDDING_MODEL

embeddings = OpenAIEmbeddings(
    model=EMBEDDING_MODEL,
    base_url=LLM_BASE_URL,
)
