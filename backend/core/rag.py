"""RAG 检索模块 - ChromaDB 向量存储"""
import chromadb
from langchain_core.documents import Document
from services.embedding import embeddings
from config import CHROMA_DIR, RAG_TOP_K

# ChromaDB 持久化客户端
chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_or_create_collection(knowledge_base_id: str):
    """获取或创建知识库对应的 collection"""
    return chroma_client.get_or_create_collection(
        name=f"kb_{knowledge_base_id}",
        metadata={"hnsw:space": "cosine"},
    )


async def add_documents(knowledge_base_id: str, documents: list[Document]) -> int:
    """将文档块添加到向量库"""
    if not documents:
        return 0

    # 防御性校验：过滤 page_content 为空或纯空白的文档
    valid_docs = [doc for doc in documents if doc.page_content and doc.page_content.strip()]
    if not valid_docs:
        return 0

    collection = get_or_create_collection(knowledge_base_id)

    # 分批处理，每批最多 50 条，避免 Embedding API 单次请求过大
    BATCH_SIZE = 50
    total_added = 0

    for batch_start in range(0, len(valid_docs), BATCH_SIZE):
        batch = valid_docs[batch_start:batch_start + BATCH_SIZE]
        texts = [doc.page_content for doc in batch]
        metadatas = [doc.metadata for doc in batch]
        ids = [f"{knowledge_base_id}_{doc.metadata['source']}_{doc.metadata['chunk_index']}" for doc in batch]

        # 批量生成 embedding
        vectors = await embeddings.aembed_documents(texts)

        collection.add(
            ids=ids,
            embeddings=vectors,
            documents=texts,
            metadatas=metadatas,
        )
        total_added += len(batch)

    return total_added


async def search(knowledge_base_id: str, query: str, top_k: int = RAG_TOP_K) -> list[str]:
    """语义检索"""
    try:
        collection = chroma_client.get_collection(name=f"kb_{knowledge_base_id}")
    except Exception:
        return []

    query_vector = await embeddings.aembed_query(query)
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
    )

    return results.get("documents", [[]])[0]


def delete_collection(knowledge_base_id: str):
    """删除知识库对应的 collection"""
    try:
        chroma_client.delete_collection(name=f"kb_{knowledge_base_id}")
    except Exception:
        pass
