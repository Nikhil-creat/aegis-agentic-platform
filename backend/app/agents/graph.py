"""
Core LangGraph multi-agent orchestration.

Implements a ReAct (Reason + Act) loop across a graph of specialized nodes:
  planner -> tool_router -> executor -> reflector -> (loop | finalize)

Features:
  - Dynamic task decomposition (planner node)
  - Tool routing to RAG / code-exec / vision tools
  - Self-reflection + automated error self-correction loop
  - Input/output guardrail enforcement at graph boundaries

Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from tenacity import retry, stop_after_attempt, wait_exponential

from app.agents.tools import TOOL_REGISTRY, execute_tool
from app.core.config import get_settings
from app.core.guardrails import guardrails_engine

settings = get_settings()

MAX_SELF_CORRECTION_ATTEMPTS = 3


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    plan: list[str]
    current_step: int
    tool_results: Annotated[list[dict[str, Any]], operator.add]
    error_count: int
    final_answer: str | None
    trace_log: Annotated[list[dict[str, Any]], operator.add]


def _llm(temperature: float = 0.0) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.DEFAULT_LLM_MODEL,
        temperature=temperature,
        api_key=settings.OPENAI_API_KEY,
    )


SYSTEM_PROMPT = (
    "You are Aegis, an autonomous engineering agent. Decompose the user's request "
    "into concrete steps, use the available tools (rag_search, execute_code, "
    "analyze_image) when needed, verify your own outputs, and self-correct on "
    "failure before answering. Available tools: {tools}"
)


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def guardrail_input_node(state: AgentState) -> AgentState:
    last_human = next((m for m in reversed(state["messages"]) if isinstance(m, HumanMessage)), None)
    if last_human:
        result = guardrails_engine.screen_input(last_human.content)
        if not result.allowed:
            return {
                **state,
                "final_answer": "Request blocked by safety guardrails: " + (result.reason or "policy violation"),
                "trace_log": [{"node": "guardrail_input", "blocked": True, "reason": result.reason}],
            }
    return {**state, "trace_log": [{"node": "guardrail_input", "blocked": False}]}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _invoke_planner(messages: list[BaseMessage]) -> AIMessage:
    llm = _llm()
    tool_names = ", ".join(TOOL_REGISTRY.keys())
    system = SystemMessage(content=SYSTEM_PROMPT.format(tools=tool_names))
    return llm.invoke([system, *messages])


def planner_node(state: AgentState) -> AgentState:
    if state.get("final_answer"):
        return state  # short-circuit if guardrail already blocked
    response = _invoke_planner(state["messages"])
    # naive decomposition: split on newlines that look like steps
    steps = [line.strip("- ").strip() for line in response.content.split("\n") if line.strip()]
    return {
        **state,
        "messages": [response],
        "plan": steps or [response.content],
        "current_step": 0,
        "trace_log": [{"node": "planner", "plan": steps}],
    }


def tool_router_node(state: AgentState) -> AgentState:
    """Decide which tool (if any) the current plan step requires."""
    if state.get("final_answer"):
        return state
    step_idx = state["current_step"]
    if step_idx >= len(state["plan"]):
        return {**state, "trace_log": [{"node": "tool_router", "action": "no_more_steps"}]}

    step_text = state["plan"][step_idx].lower()
    tool_name = "none"
    if any(k in step_text for k in ("run", "execute", "compile", "code")):
        tool_name = "execute_code"
    elif any(k in step_text for k in ("search", "retrieve", "lookup", "docs")):
        tool_name = "rag_search"
    elif any(k in step_text for k in ("image", "diagram", "screenshot", "visual")):
        tool_name = "analyze_image"

    return {**state, "trace_log": [{"node": "tool_router", "selected_tool": tool_name, "step": step_text}]}


async def executor_node(state: AgentState) -> AgentState:
    if state.get("final_answer"):
        return state
    step_idx = state["current_step"]
    if step_idx >= len(state["plan"]):
        return state

    last_route = state["trace_log"][-1] if state["trace_log"] else {}
    tool_name = last_route.get("selected_tool", "none")
    step_text = state["plan"][step_idx]

    result: dict[str, Any] = {"step": step_text, "tool": tool_name}
    try:
        if tool_name != "none":
            output = await execute_tool(tool_name, step_text)
            result["output"] = output
            result["success"] = True
        else:
            result["output"] = None
            result["success"] = True
    except Exception as exc:  # noqa: BLE001 — captured for self-correction loop
        result["output"] = str(exc)
        result["success"] = False

    return {
        **state,
        "tool_results": [result],
        "current_step": step_idx + 1,
        "error_count": state["error_count"] + (0 if result["success"] else 1),
        "trace_log": [{"node": "executor", **result}],
    }


def reflector_node(state: AgentState) -> AgentState:
    """Self-reflection: inspect the latest tool result; if it failed, decide
    whether to retry (self-correction) or bail out gracefully."""
    if state.get("final_answer"):
        return state
    if not state["tool_results"]:
        return {**state, "trace_log": [{"node": "reflector", "verdict": "no_results_yet"}]}

    latest = state["tool_results"][-1]
    if latest["success"]:
        return {**state, "trace_log": [{"node": "reflector", "verdict": "step_ok"}]}

    if state["error_count"] >= MAX_SELF_CORRECTION_ATTEMPTS:
        return {
            **state,
            "final_answer": (
                f"I attempted self-correction {MAX_SELF_CORRECTION_ATTEMPTS} times but the step "
                f"'{latest['step']}' kept failing: {latest['output']}. Escalating to a human operator."
            ),
            "trace_log": [{"node": "reflector", "verdict": "max_retries_exceeded"}],
        }

    # self-correction: re-insert a revised version of the failing step
    corrected_step = f"Retry with corrected approach: {latest['step']} (previous error: {latest['output']})"
    new_plan = list(state["plan"])
    new_plan.insert(state["current_step"], corrected_step)
    return {
        **state,
        "plan": new_plan,
        "trace_log": [{"node": "reflector", "verdict": "self_correcting", "corrected_step": corrected_step}],
    }


def finalize_node(state: AgentState) -> AgentState:
    if state.get("final_answer"):
        output_check = guardrails_engine.screen_output(state["final_answer"])
        final = output_check.redacted_text or state["final_answer"]
        return {**state, "final_answer": final}

    summary_llm = _llm(temperature=0.2)
    tool_summary = "\n".join(
        f"- {r['step']}: {r.get('output')}" for r in state["tool_results"]
    )
    prompt = (
        "Summarize the following completed steps into a final, direct answer "
        f"for the user:\n{tool_summary}"
    )
    response = summary_llm.invoke([HumanMessage(content=prompt)])
    output_check = guardrails_engine.screen_output(response.content)
    final_text = output_check.redacted_text if output_check.allowed else "Response blocked by output guardrails."
    return {**state, "final_answer": final_text, "trace_log": [{"node": "finalize", "blocked": not output_check.allowed}]}


# ---------------------------------------------------------------------------
# Routing logic
# ---------------------------------------------------------------------------

def route_after_guardrail(state: AgentState) -> Literal["planner", "finalize"]:
    return "finalize" if state.get("final_answer") else "planner"


def route_after_reflect(state: AgentState) -> Literal["tool_router", "finalize"]:
    if state.get("final_answer"):
        return "finalize"
    if state["current_step"] >= len(state["plan"]):
        return "finalize"
    return "tool_router"


def build_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("guardrail_input", guardrail_input_node)
    graph.add_node("planner", planner_node)
    graph.add_node("tool_router", tool_router_node)
    graph.add_node("executor", executor_node)
    graph.add_node("reflector", reflector_node)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("guardrail_input")
    graph.add_conditional_edges("guardrail_input", route_after_guardrail, {"planner": "planner", "finalize": "finalize"})
    graph.add_edge("planner", "tool_router")
    graph.add_edge("tool_router", "executor")
    graph.add_edge("executor", "reflector")
    graph.add_conditional_edges("reflector", route_after_reflect, {"tool_router": "tool_router", "finalize": "finalize"})
    graph.add_edge("finalize", END)

    return graph.compile()


agent_graph = build_agent_graph()


async def run_agent(user_input: str) -> AgentState:
    initial_state: AgentState = {
        "messages": [HumanMessage(content=user_input)],
        "plan": [],
        "current_step": 0,
        "tool_results": [],
        "error_count": 0,
        "final_answer": None,
        "trace_log": [],
    }
    return await agent_graph.ainvoke(initial_state)
