"""Cohere Rerank 4 (Pro and Fast) through OpenRouter's rerank endpoint, which routes to Cohere and returns the exact
billed cost per call (usage.cost) along with Cohere's search units. Same model weights as Cohere's own endpoint
(the response names them rerank-v4.0-pro / rerank-v4.0-fast)."""
from __future__ import annotations

from common import Call, QueryResult, env, post_json

URL = "https://openrouter.ai/api/v1/rerank"


class Cohere:
    def __init__(self, model: str, key: str):
        self.model, self.key = model, key

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        headers = {"Authorization": f"Bearer {env('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}
        body = {"model": self.model, "query": query, "documents": docs, "top_n": len(docs)}
        status, resp, ms, _ = post_json(URL, headers, body)
        if status != 200 or not isinstance(resp, dict) or "results" not in resp:
            return QueryResult([None] * len(docs), [Call(ms, status, {}, 0.0, raw=str(resp)[:500], error=f"HTTP {status}")])
        usage = resp.get("usage") or {}
        cost = float(usage.get("cost") or 0.0)
        scores: list[float | None] = [None] * len(docs)
        for r in resp["results"]:
            scores[r["index"]] = float(r["relevance_score"])
            r.pop("document", None)   # the echoed passage text is already in candidates/; keep the cache small
        return QueryResult(scores, [Call(ms, status, {"search_units": usage.get("search_units"), "served_model": resp.get("model"),
                                                     "provider": resp.get("provider")}, cost, raw=resp)])
