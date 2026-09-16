"""ZeroEntropy zerank-2. Billed per token; the response reports total_tokens."""
from __future__ import annotations

from common import PRICES, Call, QueryResult, env, post_json

URL = "https://api.zeroentropy.dev/v1/models/rerank"


class Zerank:
    def __init__(self, model: str):
        self.model, self.key = model, model

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        headers = {"Authorization": f"Bearer {env('ZEROENTROPY_API_KEY')}", "Content-Type": "application/json"}
        body = {"model": self.model, "query": query, "documents": docs, "top_n": len(docs)}
        status, resp, ms, _ = post_json(URL, headers, body)
        if status != 200 or not isinstance(resp, dict):
            return QueryResult([None] * len(docs), [Call(ms, status, {}, 0.0, raw=str(resp)[:500], error=f"HTTP {status}")])
        tokens = int(resp.get("total_tokens") or 0)
        usage = {"total_tokens": tokens, "total_bytes": resp.get("total_bytes"),
                 "inference_latency_s": resp.get("inference_latency"), "latency_mode": resp.get("actual_latency_mode")}
        scores: list[float | None] = [None] * len(docs)
        for r in resp["results"]:
            scores[r["index"]] = float(r["relevance_score"])
        return QueryResult(scores, [Call(ms, status, usage, tokens * PRICES["zerank-2"]["per_m_tokens"] / 1e6, raw=resp)])
