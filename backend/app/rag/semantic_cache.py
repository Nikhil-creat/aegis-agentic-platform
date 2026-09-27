"""
Redis semantic cache: stores (query embedding -> retrieved docs) so that
identical or structurally-similar queries skip the full retrieval pipeline.

Similarity is computed via cosine distance between the incoming query's
embedding and cached query embeddings, stored as a Redis hash + a small
in-memory index refreshed on read (swap for RediSearch/pgvector at scale).

Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

import numpy as np
import redis.asyncio as redis
from langchain_openai import OpenAIEmbeddings

from app.core.config import get_settings

settings = get_settings()
CACHE_PREFIX = "semcache:"


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-8))


class SemanticCache:
    def __init__(self, threshold: float = 0.92, max_scan: int = 500) -> None:
        self._redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self._embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
        self._threshold = threshold
        self._max_scan = max_scan

    async def get(self, query: str) -> list[dict[str, Any]] | None:
        query_vec = np.array(await self._embeddings.aembed_query(query))

        cursor = 0
        best_score, best_entry = 0.0, None
        scanned = 0
        while scanned < self._max_scan:
            cursor, keys = await self._redis.scan(cursor=cursor, match=f"{CACHE_PREFIX}*", count=100)
            for key in keys:
                raw = await self._redis.get(key)
                if not raw:
                    continue
                entry = json.loads(raw)
                cached_vec = np.array(entry["embedding"])
                score = _cosine(query_vec, cached_vec)
                if score > best_score:
                    best_score, best_entry = score, entry
                scanned += 1
            if cursor == 0:
                break

        if best_entry and best_score >= self._threshold:
            return best_entry["documents"]
        return None

    async def set(self, query: str, documents: list[dict[str, Any]], ttl_seconds: int = 3600) -> None:
        query_vec = await self._embeddings.aembed_query(query)
        key = CACHE_PREFIX + hashlib.sha256(query.encode()).hexdigest()
        payload = json.dumps({"query": query, "embedding": query_vec, "documents": documents})
        await self._redis.set(key, payload, ex=ttl_seconds)
