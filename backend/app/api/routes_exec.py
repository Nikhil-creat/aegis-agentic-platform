"""
Secure code-execution routes.
Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.execution.language_configs import LANGUAGE_CONFIGS
from app.execution.sandbox_manager import SandboxManager
from app.models.schemas import CodeExecRequest, CodeExecResponse

router = APIRouter(prefix="/api/v1/execute", tags=["execution"])
_sandbox = SandboxManager()


@router.get("/languages")
async def list_languages() -> dict:
    return {"supported_languages": list(LANGUAGE_CONFIGS.keys())}


@router.post("/", response_model=CodeExecResponse)
async def execute_code(payload: CodeExecRequest, user: str = Depends(get_current_user)) -> CodeExecResponse:
    if payload.language not in LANGUAGE_CONFIGS:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {payload.language}")
    result = await _sandbox.run(language=payload.language, code=payload.code)
    return CodeExecResponse(**result)
