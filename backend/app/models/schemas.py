"""
Pydantic v2 schemas for API request/response validation.
Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AgentRunRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    session_id: str | None = None


class AgentRunResponse(BaseModel):
    session_id: str
    final_answer: str
    trace_log: list[dict]
    tool_results: list[dict]


class CodeExecRequest(BaseModel):
    language: str
    code: str = Field(min_length=1, max_length=20_000)


class CodeExecResponse(BaseModel):
    job_id: str
    success: bool
    output: str
    error: str | None = None
    duration_seconds: float


class RagQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)


class AuditLogEntry(BaseModel):
    id: int
    user_id: str
    action: str
    detail: str
    created_at: datetime

    class Config:
        from_attributes = True
