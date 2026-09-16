"""The floor: keep BM25's own order. Scores are the BM25 values the candidate builder stored."""
from __future__ import annotations

from common import QueryResult


class BM25Order:
    key = "bm25"

    def rerank(self, query: str, docs: list[str], bm25: list[float] | None = None) -> QueryResult:
        return QueryResult(scores=list(bm25 or []), calls=[])
