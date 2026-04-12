"""LangGraph Agent - 集成 RAG + 记忆的对话 Agent"""
from typing import TypedDict, Annotated, AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from sqlalchemy.ext.asyncio import AsyncSession

from services.llm import llm
from core.rag import search as rag_search
from core.memory import (
    load_short_term_messages,
    load_long_term_summary,
    save_message,
    maybe_update_long_term_memory,
)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    session_id: str
    knowledge_base_id: str | None
    rag_context: str
    db: AsyncSession


# ── 节点：加载记忆 ──
async def load_memory_node(state: AgentState) -> dict:
    """加载长期记忆摘要，注入为 system message"""
    db = state["db"]
    session_id = state["session_id"]

    # 加载历史消息
    history = await load_short_term_messages(db, session_id)

    # 加载长期摘要
    summary = await load_long_term_summary(db, session_id)

    messages = []
    if summary:
        messages.append(SystemMessage(content=f"以下是之前对话的摘要，请参考：\n{summary}"))
    messages.extend(history)

    # 追加当前用户输入（state["messages"] 中最后一条）
    current_input = state["messages"][-1] if state["messages"] else None
    if current_input:
        messages.append(current_input)

    return {"messages": messages}


# ── 节点：RAG 检索 ──
async def rag_retrieve_node(state: AgentState) -> dict:
    """从知识库检索相关内容"""
    kb_id = state.get("knowledge_base_id")
    if not kb_id:
        return {"rag_context": ""}

    # 取最后一条用户消息作为查询
    query = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            query = msg.content
            break

    if not query:
        return {"rag_context": ""}

    docs = await rag_search(kb_id, query)
    context = "\n---\n".join(docs) if docs else ""
    return {"rag_context": context}


# ── 节点：生成回复 ──
async def chatbot_node(state: AgentState) -> dict:
    """调用 LLM 生成回复"""
    messages = list(state["messages"])

    # 如果有 RAG 上下文，注入到消息中
    rag_context = state.get("rag_context", "")
    if rag_context:
        rag_msg = SystemMessage(
            content=f"以下是从知识库中检索到的相关信息，请参考回答用户问题：\n\n{rag_context}"
        )
        # 插入到最后一条用户消息之前
        messages.insert(-1, rag_msg)

    response = await llm.ainvoke(messages)
    return {"messages": [response]}


# ── 节点：保存记忆 ──
async def save_memory_node(state: AgentState) -> dict:
    """保存消息并可能更新长期记忆"""
    db = state["db"]
    session_id = state["session_id"]

    # 保存用户消息
    for msg in state["messages"]:
        if isinstance(msg, HumanMessage):
            last_human = msg
    await save_message(db, session_id, "human", last_human.content)

    # 保存 AI 回复（最后一条）
    ai_msg = state["messages"][-1]
    if isinstance(ai_msg, AIMessage):
        await save_message(db, session_id, "ai", ai_msg.content)

    # 异步检查是否需要更新长期记忆
    await maybe_update_long_term_memory(db, session_id)

    return {}


# ── 条件：是否需要 RAG ──
def should_retrieve(state: AgentState) -> str:
    if state.get("knowledge_base_id"):
        return "retrieve"
    return "skip"


# ── 构建图 ──
def build_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("load_memory", load_memory_node)
    graph.add_node("rag_retrieve", rag_retrieve_node)
    graph.add_node("chatbot", chatbot_node)
    graph.add_node("save_memory", save_memory_node)

    graph.add_edge(START, "load_memory")
    graph.add_conditional_edges(
        "load_memory",
        should_retrieve,
        {"retrieve": "rag_retrieve", "skip": "chatbot"},
    )
    graph.add_edge("rag_retrieve", "chatbot")
    graph.add_edge("chatbot", "save_memory")
    graph.add_edge("save_memory", END)

    return graph.compile()


# 全局 Agent 实例
agent = build_agent_graph()


async def chat(
    db: AsyncSession,
    session_id: str,
    user_message: str,
    knowledge_base_id: str | None = None,
) -> str:
    """执行一次对话"""
    result = await agent.ainvoke({
        "messages": [HumanMessage(content=user_message)],
        "session_id": session_id,
        "knowledge_base_id": knowledge_base_id,
        "rag_context": "",
        "db": db,
    })

    # 返回 AI 回复
    ai_msg = result["messages"][-1]
    return ai_msg.content


async def chat_stream(
    db: AsyncSession,
    session_id: str,
    user_message: str,
    knowledge_base_id: str | None = None,
) -> AsyncGenerator[str, None]:
    """流式对话 - 逐步返回 AI 回复"""
    # 先执行记忆加载和 RAG 检索
    messages = []

    # 加载历史
    history = await load_short_term_messages(db, session_id)
    summary = await load_long_term_summary(db, session_id)

    if summary:
        messages.append(SystemMessage(content=f"以下是之前对话的摘要，请参考：\n{summary}"))
    messages.extend(history)

    # RAG 检索
    if knowledge_base_id:
        docs = await rag_search(knowledge_base_id, user_message)
        if docs:
            rag_context = "\n---\n".join(docs)
            messages.append(SystemMessage(
                content=f"以下是从知识库中检索到的相关信息，请参考回答用户问题：\n\n{rag_context}"
            ))

    messages.append(HumanMessage(content=user_message))

    # 流式生成
    full_response = ""
    async for chunk in llm.astream(messages):
        if chunk.content:
            full_response += chunk.content
            yield chunk.content

    # 保存消息
    await save_message(db, session_id, "human", user_message)
    await save_message(db, session_id, "ai", full_response)
    await maybe_update_long_term_memory(db, session_id)
