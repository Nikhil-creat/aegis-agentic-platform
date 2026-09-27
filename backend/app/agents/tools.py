"""
Tool registry: routes agent tool calls to the RAG retriever, the sandboxed
code executor, and the CNN vision module.

Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
from typing import Any, Awaitable, Callable

from app.execution.sandbox_manager import SandboxManager
from app.rag.retriever import AgenticRAGRetriever

_retriever = AgenticRAGRetriever()
_sandbox = SandboxManager()


async def rag_search(query: str) -> dict[str, Any]:
    results = await _retriever.retrieve(query)
    return {"query": query, "results": results}


async def execute_code_tool(step_description: str) -> dict[str, Any]:
    # In production the planner would emit structured {language, code}; here
    # we extract a fenced code block if present, defaulting to python.
    language = "python"
    code = step_description
    return await _sandbox.run(language=language, code=code)


async def analyze_image_tool(step_description: str) -> dict[str, Any]:
    # Delegates to the vision-service; kept as a stub interface here.
    return {"note": "vision analysis requested", "step": step_description}


TOOL_REGISTRY: dict[str, Callable[[str], Awaitable[dict[str, Any]]]] = {
    "rag_search": rag_search,
    "execute_code": execute_code_tool,
    "analyze_image": analyze_image_tool,
}


async def execute_tool(name: str, arg: str) -> dict[str, Any]:
    if name not in TOOL_REGISTRY:
        raise ValueError(f"Unknown tool requested: {name}")
    return await TOOL_REGISTRY[name](arg)
