"""
Advanced Agentic RAG Pipeline.

Multi-hop retrieval with:
  1. Semantic cache lookup (Redis) — short-circuits repeated/similar queries
  2. Query expansion (LLM-generated paraphrases / sub-questions)
  3. Dense vector retrieval from Qdrant across expanded queries
  4. Cross-encoder reranking of the merged candidate pool
  5. Cache write-back of the final answer's embedding

Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from qdrant_client import AsyncQdrantClient
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import get_settings
from app.rag.reranker import CrossEncoderReranker
from app.rag.semantic_cache import SemanticCache

settings = get_settings()

COLLECTION_NAME = "aegis_knowledge_base"


class AgenticRAGRetriever:
    def __init__(self) -> None:
        self._qdrant = AsyncQdrantClient(url=settings.QDRANT_URL)
        self._embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        self._reranker = CrossEncoderReranker(model_name=settings.RERANKER_MODEL)
        self._cache = SemanticCache(threshold=settings.SEMANTIC_CACHE_THRESHOLD)
        self._expansion_llm = ChatOpenAI(model=settings.DEFAULT_LLM_MODEL, temperature=0.3, api_key=settings.OPENAI_API_KEY)

    # ------------------------------------------------------------------
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def _expand_query(self, query: str) -> list[str]:
        prompt = (
            "Generate 3 diverse reformulations / sub-questions that would help "
            f"retrieve documents relevant to: '{query}'. Return one per line, no numbering."
        )
        response = await self._expansion_llm.ainvoke(prompt)
        variants = [line.strip("- ").strip() for line in response.content.split("\n") if line.strip()]
        return [query] + variants[:3]

    async def _vector_search(self, query: str, top_k: int) -> list[dict[str, Any]]:
        vector = await self._embeddings.aembed_query(query)
        hits = await self._qdrant.search(collection_name=COLLECTION_NAME, query_vector=vector, limit=top_k)
        return [
            {"id": hit.id, "score": hit.score, "text": hit.payload.get("text", ""), "metadata": hit.payload}
            for hit in hits
        ]

    # ------------------------------------------------------------------
    async def retrieve(self, query: str) -> dict[str, Any]:
        cached = await self._cache.get(query)
        if cached is not None:
            return {"source": "semantic_cache", "documents": cached}

        expanded_queries = await self._expand_query(query)

        candidate_pool: dict[str, dict[str, Any]] = {}
        for sub_query in expanded_queries:
            hits = await self._vector_search(sub_query, top_k=settings.TOP_K_RETRIEVAL)
            for hit in hits:
                candidate_pool.setdefault(hit["id"], hit)  # dedupe by doc id

        candidates = list(candidate_pool.values())
        reranked = self._reranker.rerank(query, candidates, top_k=settings.TOP_K_RERANKED)

        await self._cache.set(query, reranked)
        return {"source": "live_retrieval", "documents": reranked, "expanded_queries": expanded_queries}
