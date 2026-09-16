"""Chat-model baselines through OpenRouter, pinned to one provider (no fallbacks) so every call hits the same weights.
OpenRouter is asked to include the exact billed cost in each response, and thinking is switched off so the first
output token is the answer.

- LLMYesProb   : one call per (query, passage), yes/no, scored by the probability on "yes" as the first token
                 (temperature 0, one output token, top-10 token probabilities). The baseline the Kaggle grandmaster
                 asked for.
- LLMJsonScores: one call per query, all 30 passages, JSON with a 0-100 score per passage. The fair twin to Jev's
                 one-call modes.
"""
from __future__ import annotations

import json
import math

from common import Call, QueryResult, env, post_json

URL = "https://openrouter.ai/api/v1/chat/completions"
SYSTEM_YESNO = "You judge whether a passage contains the information needed to answer or verify a query. Reply with exactly one word: yes or no."
SYSTEM_JSON = "You score passages for how well they contain the information needed to answer or verify a query. Output only JSON."


def _pid(i: int) -> str:
    return f"p{i + 1:02d}"


def yes_no_probs(top_logprobs: list[dict]) -> tuple[float, float]:
    """Mass on 'yes'-like and 'no'-like first tokens (case and leading-space insensitive)."""
    p_yes = p_no = 0.0
    for t in top_logprobs:
        tok = t["token"].strip().lower()
        p = math.exp(t["logprob"])
        if tok == "yes":
            p_yes += p
        elif tok == "no":
            p_no += p
    return p_yes, p_no


def _base(model: str, provider: str) -> dict:
    return {"model": model, "temperature": 0, "usage": {"include": True}, "reasoning": {"effort": "none"},
            "provider": {"order": [provider], "allow_fallbacks": False}}


def _headers() -> dict:
    return {"Authorization": f"Bearer {env('OPENROUTER_API_KEY')}", "Content-Type": "application/json"}


class LLMYesProb:
    def __init__(self, model: str, key: str, provider: str):
        self.model, self.key, self.provider = model, key, provider

    def _one(self, query: str, doc: str) -> tuple[Call, float | None, dict]:
        from rerankers import RELEVANCE_QUESTION
        body = dict(_base(self.model, self.provider),
                    messages=[{"role": "system", "content": SYSTEM_YESNO},
                              {"role": "user", "content": f"Query: {query}\n\nPassage: {doc}\n\n{RELEVANCE_QUESTION} Answer yes or no."}],
                    max_tokens=2, logprobs=True, top_logprobs=10)
        status, resp, ms, _ = post_json(URL, _headers(), body)
        if status != 200 or not isinstance(resp, dict) or "choices" not in resp:
            return Call(ms, status, {}, 0.0, raw=str(resp)[:500], error=f"HTTP {status}"), None, {}
        usage = resp.get("usage") or {}
        cost = float(usage.get("cost") or 0.0)
        ch = resp["choices"][0]
        content = ((ch.get("logprobs") or {}).get("content") or [])
        if not content:
            return Call(ms, status, usage, cost, raw=resp, error="no logprobs in response"), None, {}
        p_yes, p_no = yes_no_probs(content[0].get("top_logprobs") or [])
        score = p_yes / (p_yes + p_no) if (p_yes + p_no) > 0 else p_yes
        return Call(ms, status, usage, cost, raw=resp), score, {"p_yes_raw": p_yes, "p_no_raw": p_no}

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        scores, calls, raw_yes = [], [], []
        for d in docs:
            call, s, ex = self._one(query, d)
            calls.append(call)
            scores.append(s)
            raw_yes.append(ex.get("p_yes_raw"))
        return QueryResult(scores, calls, extra={"p_yes_raw": raw_yes, "provider": self.provider})


class LLMJsonScores:
    def __init__(self, model: str, key: str, provider: str):
        self.model, self.key, self.provider = model, key, provider

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        from rerankers import RELEVANCE_QUESTION
        ids = [_pid(i) for i in range(len(docs))]
        listing = "\n\n".join(f"[{pid}] {d}" for pid, d in zip(ids, docs))
        example = "{" + ", ".join(f'"{pid}": 0' for pid in ids[:3]) + ", ...}"
        user = (f"Query: {query}\n\nPassages:\n{listing}\n\n{RELEVANCE_QUESTION[:-1]}, for each passage? "
                f"Score every passage from 0 (nothing needed is there) to 100 (it fully contains it). "
                f"Output JSON with all {len(ids)} ids and integer scores, like {example}")
        body = dict(_base(self.model, self.provider),
                    messages=[{"role": "system", "content": SYSTEM_JSON}, {"role": "user", "content": user}],
                    max_tokens=600, response_format={"type": "json_object"})
        status, resp, ms, _ = post_json(URL, _headers(), body)
        if status != 200 or not isinstance(resp, dict) or "choices" not in resp:
            return QueryResult([None] * len(docs), [Call(ms, status, {}, 0.0, raw=str(resp)[:500], error=f"HTTP {status}")])
        usage = resp.get("usage") or {}
        cost = float(usage.get("cost") or 0.0)
        text = (resp["choices"][0]["message"].get("content") or "").strip()
        try:
            parsed = json.loads(text)
            if not isinstance(parsed, dict):
                raise ValueError("not an object")
        except ValueError as e:
            return QueryResult([None] * len(docs), [Call(ms, status, usage, cost, raw=resp, error=f"bad JSON: {e}")])
        scores, missing = [], 0
        for pid in ids:
            v = parsed.get(pid)
            try:
                scores.append(max(0.0, min(1.0, float(v) / 100.0)))
            except (TypeError, ValueError):
                scores.append(0.0)
                missing += 1
        return QueryResult(scores, [Call(ms, status, usage, cost, raw=resp)], extra={"missing_ids": missing, "provider": self.provider})
