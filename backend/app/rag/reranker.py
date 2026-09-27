"""
Cross-encoder / BGE reranker for high-precision retrieval reordering.
Falls back to Cohere Rerank API if `COHERE_API_KEY` is configured.

Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
from typing import Any

from sentence_transformers import CrossEncoder


class CrossEncoderReranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base") -> None:
        # Loaded lazily/once per process; CPU inference is fine at this scale.
        self._model = CrossEncoder(model_name, max_length=512)

    def rerank(self, query: str, candidates: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
        if not candidates:
            return []
        pairs = [(query, c["text"]) for c in candidates]
        scores = self._model.predict(pairs)
        for candidate, score in zip(candidates, scores):
            candidate["rerank_score"] = float(score)
        ranked = sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)
        return ranked[:top_k]
