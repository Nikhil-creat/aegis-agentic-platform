"""
Agent routes: synchronous run, async (Celery) run, and SSE-streamed
thought-log for live UI updates.

Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
import asyncio
import json
import uuid

from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse

from app.agents.graph import run_agent
from app.core.security import get_current_user
from app.models.schemas import AgentRunRequest, AgentRunResponse
from workers.celery_app import run_agent_task

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.post("/run", response_model=AgentRunResponse)
async def run_agent_sync(payload: AgentRunRequest, user: str = Depends(get_current_user)) -> AgentRunResponse:
    session_id = payload.session_id or str(uuid.uuid4())
    state = await run_agent(payload.prompt)
    return AgentRunResponse(
        session_id=session_id,
        final_answer=state["final_answer"] or "",
        trace_log=state["trace_log"],
        tool_results=state["tool_results"],
    )


@router.post("/run-async")
async def run_agent_async(payload: AgentRunRequest, user: str = Depends(get_current_user)) -> dict:
    session_id = payload.session_id or str(uuid.uuid4())
    task = run_agent_task.delay(payload.prompt, session_id)
    return {"task_id": task.id, "session_id": session_id, "status": "queued"}


@router.get("/stream/{session_id}")
async def stream_agent_thoughts(session_id: str, prompt: str, user: str = Depends(get_current_user)):
    """Streams the agent's step-by-step trace log live via Server-Sent Events."""

    async def event_generator():
        state = {
            "messages": [],
            "plan": [],
            "current_step": 0,
            "tool_results": [],
            "error_count": 0,
            "final_answer": None,
            "trace_log": [],
        }
        from langchain_core.messages import HumanMessage

        state["messages"] = [HumanMessage(content=prompt)]

        from app.agents.graph import agent_graph

        async for chunk in agent_graph.astream(state):
            for node_name, node_state in chunk.items():
                yield {
                    "event": "agent_step",
                    "data": json.dumps({"node": node_name, "trace": node_state.get("trace_log", [])}),
                }
            await asyncio.sleep(0)  # yield control for backpressure

        yield {"event": "done", "data": json.dumps({"session_id": session_id})}

    return EventSourceResponse(event_generator())
