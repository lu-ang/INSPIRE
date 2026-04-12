"""知识库管理 API"""
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import KnowledgeBase, Document
from services.document_loader import parse_and_split, SUPPORTED_EXTENSIONS
from core.rag import add_documents, delete_collection
from config import UPLOAD_DIR
from utils.logger import log_operation

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.get("")
async def list_knowledge_bases(db: AsyncSession = Depends(get_db)):
    """获取所有知识库"""
    result = await db.execute(
        select(KnowledgeBase).order_by(KnowledgeBase.created_at.desc())
    )
    kbs = result.scalars().all()
    items = []
    for kb in kbs:
        doc_result = await db.execute(
            select(Document).where(Document.knowledge_base_id == kb.id)
        )
        docs = doc_result.scalars().all()
        items.append({
            "id": kb.id,
            "name": kb.name,
            "description": kb.description,
            "created_at": kb.created_at.isoformat(),
            "document_count": len(docs),
            "documents": [
                {"id": d.id, "filename": d.filename, "file_type": d.file_type, "chunk_count": d.chunk_count}
                for d in docs
            ],
        })
    return items


@router.post("")
async def create_knowledge_base(
    name: str = Form(...),
    description: str = Form(""),
    db: AsyncSession = Depends(get_db),
):
    """创建知识库"""
    kb = KnowledgeBase(name=name, description=description)
    db.add(kb)
    await db.commit()
    await db.refresh(kb)
    await log_operation(db, "knowledge", "create_kb", f"id={kb.id}, name={name}")
    return {"id": kb.id, "name": kb.name}


@router.post("/{kb_id}/upload")
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """上传文档到知识库"""
    # 检查知识库是否存在
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        return {"error": "知识库不存在"}

    # 检查文件格式
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return {"error": f"不支持的文件格式: {ext}，支持: {', '.join(SUPPORTED_EXTENSIONS)}"}

    # 保存文件
    kb_upload_dir = UPLOAD_DIR / kb_id
    kb_upload_dir.mkdir(exist_ok=True)
    file_path = kb_upload_dir / file.filename
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    try:
        # 解析并切分文档
        docs = parse_and_split(str(file_path), kb_id)

        if not docs:
            await log_operation(db, "knowledge", "upload_doc_empty", f"kb={kb_id}, file={file.filename}, 文件内容为空或无法提取有效文本")
            return {"error": "文件内容为空或无法提取有效文本，请检查文件内容后重试"}

        # 添加到向量库
        chunk_count = await add_documents(kb_id, docs)

        if chunk_count == 0:
            await log_operation(db, "knowledge", "upload_doc_empty", f"kb={kb_id}, file={file.filename}, 所有分块均无效")
            return {"error": "文件分块后无有效内容，请检查文件内容后重试"}

        # 记录到数据库
        doc_record = Document(
            knowledge_base_id=kb_id,
            filename=file.filename,
            file_type=ext,
            chunk_count=chunk_count,
        )
        db.add(doc_record)
        await db.commit()

        await log_operation(db, "knowledge", "upload_doc", f"kb={kb_id}, file={file.filename}, chunks={chunk_count}")
        return {"filename": file.filename, "chunk_count": chunk_count}

    except Exception as e:
        await log_operation(db, "knowledge", "upload_doc_error", str(e), level="ERROR")
        return {"error": str(e)}


@router.delete("/{kb_id}")
async def delete_knowledge_base(kb_id: str, db: AsyncSession = Depends(get_db)):
    """删除知识库"""
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == kb_id))
    kb = result.scalar_one_or_none()
    if not kb:
        return {"error": "知识库不存在"}

    # 删除向量库
    delete_collection(kb_id)

    # 删除上传文件
    kb_upload_dir = UPLOAD_DIR / kb_id
    if kb_upload_dir.exists():
        shutil.rmtree(kb_upload_dir)

    # 删除数据库记录
    await db.delete(kb)
    await db.commit()

    await log_operation(db, "knowledge", "delete_kb", f"id={kb_id}")
    return {"ok": True}
