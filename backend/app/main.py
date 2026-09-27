"""
Aegis Autonomous Agentic Platform — FastAPI Gateway.

Main router: auth, agent orchestration (sync/async/SSE), code execution,
and RAG endpoints, plus a raw WebSocket channel for bidirectional agent chat.

Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_agents import router as agents_router
from app.api.routes_auth import router as auth_router
from app.api.routes_exec import router as exec_router
from app.api.routes_rag import router as rag_router
from app.core.config import get_settings
from app.core.telemetry import setup_telemetry

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: nothing heavyweight here — sub-modules lazy-init their clients
    yield
    # shutdown: place connection-pool teardown here if needed


app = FastAPI(
    title=settings.APP_NAME,
    description="Enterprise autonomous agentic AI platform — Designed and Developed by Nikhil Chary Sriramoju",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_telemetry(app)

app.include_router(auth_router)
app.include_router(agents_router)
app.include_router(exec_router)
app.include_router(rag_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "aegis-gateway", "author": settings.AUTHOR}


@app.get("/")
async def root() -> dict:
    return {
        "name": settings.APP_NAME,
        "designed_and_developed_by": "NIKHIL CHARY SRIRAMOJU",
        "docs": "/docs",
    }


@app.websocket("/ws/agent/{session_id}")
async def agent_websocket(websocket: WebSocket, session_id: str):
    """Bidirectional channel: client sends a prompt, server streams back
    node-by-node agent trace events and the final answer."""
    await websocket.accept()
    try:
        while True:
            prompt = await websocket.receive_text()

            from langchain_core.messages import HumanMessage

            from app.agents.graph import agent_graph

            state = {
                "messages": [HumanMessage(content=prompt)],
                "plan": [],
                "current_step": 0,
                "tool_results": [],
                "error_count": 0,
                "final_answer": None,
                "trace_log": [],
            }

            async for chunk in agent_graph.astream(state):
                for node_name, node_state in chunk.items():
                    await websocket.send_json({"type": "trace", "node": node_name, "data": node_state.get("trace_log", [])})
                    if node_state.get("final_answer"):
                        await websocket.send_json({"type": "final", "answer": node_state["final_answer"]})
    except WebSocketDisconnect:
        pass
