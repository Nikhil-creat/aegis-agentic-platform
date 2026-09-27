"""
RAG query routes.
Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.models.schemas import RagQueryRequest
from app.rag.retriever import AgenticRAGRetriever

router = APIRouter(prefix="/api/v1/rag", tags=["rag"])
_retriever = AgenticRAGRetriever()


@router.post("/query")
async def query_rag(payload: RagQueryRequest, user: str = Depends(get_current_user)) -> dict:
    return await _retriever.retrieve(payload.query)
