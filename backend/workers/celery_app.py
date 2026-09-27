"""
Celery application: offloads long-running agent runs and code-compilation
jobs to background workers, backed by Redis as broker + result store.

Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
import asyncio

from celery import Celery
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.execution.sandbox_manager import SandboxManager

settings = get_settings()

celery_app = Celery(
    "aegis_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_time_limit=settings.SANDBOX_TIMEOUT_SECONDS + 30,
    worker_prefetch_multiplier=1,
)

_sandbox = SandboxManager()


@celery_app.task(name="aegis.run_agent_task", bind=True, max_retries=2)
def run_agent_task(self, prompt: str, session_id: str) -> dict:
    from app.agents.graph import run_agent  # local import avoids circular init

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=6))
    def _invoke():
        return asyncio.run(run_agent(prompt))

    try:
        result_state = _invoke()
        return {
            "session_id": session_id,
            "final_answer": result_state["final_answer"],
            "trace_log": result_state["trace_log"],
            "tool_results": result_state["tool_results"],
        }
    except Exception as exc:  # noqa: BLE001
        raise self.retry(exc=exc, countdown=5) from exc


@celery_app.task(name="aegis.run_code_task", bind=True, max_retries=1)
def run_code_task(self, language: str, code: str) -> dict:
    try:
        return asyncio.run(_sandbox.run(language=language, code=code))
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": str(exc)}
