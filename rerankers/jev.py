"""TypeSafe Jev, eight ways. Passages in a call are charged once; the questions riding on them are free, so several of
these pack many questions into one request.

Basic (mirror what a normal reranker does):
- JevNoulPair  : one call per (query, passage), one yes/no question; rank by the probability. TypeSafe's own reranking
                 cookbook pattern (docs.typesafe.ai/cookbooks/rerank_typesafe).
- JevNoulBatch : one call per query; 30 passages in the state, 30 yes/no questions (their fan-out pattern).
- JevChoice    : one call per query; one Choice over the 30 passage ids plus "none", and a yes/no "does any passage
                 answer it" (their semantic_find cookbook). Rank by the Choice probabilities; P(none) and the
                 any-probability are the model's own "nothing relevant" signals.

Outside the box:
- JevScoreBatch: 30 Score questions with a four-level rubric in one call; rank by the expected level.
- JevDuel      : the top 10 by BM25 go in the state and all 45 "which of these two is better?" Choices ride in one
                 call; rank by expected wins. Passages 11-30 keep BM25 order below.
- JevTournament: six Choices over groups of five (+none) in one call, then one final Choice among the six group
                 winners (+none). Two calls. Fixes the thinning of a 30-way Choice.
- JevCascade   : one batched yes/no call prunes 30 to 8, then per-pair yes/no on the 8. Nine calls, not 30.
- JevChoiceReversed: JevChoice with the 30 passages sent in reverse order; compared with JevChoice to measure how much
                 the ranking depends on the order of the input.
"""
from __future__ import annotations

from itertools import combinations

from common import PRICES, Call, QueryResult, env, post_json

import os

# JEV_URL / JEV_MODEL let the same request builders run against another host that speaks the same protocol: a local
# server for the open-weight Open-Jev adapters (JEV_GPU_RATE, USD per hour, then bills GPU seconds instead of tokens),
# or OpenRouter's System One endpoint (https://openrouter.ai/api/v1/systemone, model typesafe/jev-latest), which takes
# the OpenRouter key and returns the exact billed cost in usage.cost.
URL = os.environ.get("JEV_URL", "https://api.typesafe.ai/v1/systemone")
MODEL = os.environ.get("JEV_MODEL", "jev-latest")
VIA_OPENROUTER = "openrouter.ai" in URL
RUBRIC = ["The passage is off-topic for the query.",
          "The passage is on a related topic but does not supply what the query asks for.",
          "The passage partly supplies the information needed to answer or verify the query.",
          "The passage fully supplies the information needed to answer or verify the query."]


def _headers() -> dict:
    if VIA_OPENROUTER:
        key = env("OPENROUTER_API_KEY")
    else:
        key = os.environ.get("JEV_API_KEY", "") if os.environ.get("JEV_URL") else env("JEV_API_KEY")
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "Accept": "application/json"}


def _cost(usage: dict, ms: float = 0.0) -> float:
    if os.environ.get("JEV_GPU_RATE"):
        return ms / 3.6e6 * float(os.environ["JEV_GPU_RATE"])
    if "cost" in usage:          # OpenRouter bills the call and says how much
        return float(usage["cost"] or 0.0)
    p = PRICES["jev"]
    return usage.get("input_tokens", 0) * p["input_per_m"] / 1e6 + usage.get("output_tokens", 0) * p["output_per_m"] / 1e6


def _ask(state, questions: dict) -> tuple[Call, dict | None]:
    status, body, ms, _ = post_json(URL, _headers(), {"state": state, "model": MODEL, "questions": questions})
    if status != 200 or not isinstance(body, dict):
        return Call(ms, status, {}, 0.0, raw=body if isinstance(body, dict) else str(body)[:500], error=f"HTTP {status}"), None
    usage = body.get("usage") or {}
    return Call(ms, status, usage, _cost(usage, ms), raw=body), body


def _noul(instructions: str) -> dict:
    from rerankers import RELEVANCE_FALSE, RELEVANCE_TRUE
    return {"type": "noul", "instructions": instructions, "criteria": {"true": RELEVANCE_TRUE, "false": RELEVANCE_FALSE}}


def _pid(i: int) -> str:
    return f"p{i + 1:02d}"


def _state(query: str, docs: list[str], ids: list[str] | None = None) -> dict:
    ids = ids or [_pid(i) for i in range(len(docs))]
    return {"query": query, "passages": dict(zip(ids, docs))}


def _choice_questions(ids: list[str]) -> dict:
    """The Choice + any-noul pair used by JevChoice, JevTournament and JevChoiceReversed."""
    from rerankers import RELEVANCE_FALSE, RELEVANCE_TRUE
    criteria = {i: None for i in ids}
    criteria["none"] = "No listed passage contains the information needed to answer or verify the query."
    return {
        "best": {"type": "choice",
                 "instructions": "Which passage contains the information needed to answer or verify the query? Pick none if no passage does.",
                 "criteria": criteria},
        "any": {"type": "noul",
                "instructions": "Does any listed passage contain the information needed to answer or verify the query?",
                "criteria": {"true": "At least one passage " + RELEVANCE_TRUE[len("The passage "):],
                             "false": "Every passage " + RELEVANCE_FALSE[len("The passage "):]}},
    }


class JevNoulPair:
    key = "jev-noul-pair"

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        from rerankers import RELEVANCE_QUESTION
        scores, calls = [], []
        for d in docs:
            call, body = _ask({"query": query, "passage": d}, {"relevant": _noul(RELEVANCE_QUESTION)})
            calls.append(call)
            scores.append(body["answers"]["relevant"]["noul"] if body else None)
        return QueryResult(scores, calls)


def _batch_nouls(query: str, docs: list[str]) -> tuple[Call, list[float] | None]:
    from rerankers import RELEVANCE_QUESTION
    questions = {_pid(i): _noul(RELEVANCE_QUESTION.replace("the passage", f"passage {_pid(i)}")) for i in range(len(docs))}
    call, body = _ask(_state(query, docs), questions)
    return call, ([body["answers"][_pid(i)]["noul"] for i in range(len(docs))] if body else None)


class JevNoulBatch:
    key = "jev-noul-batch"

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        call, scores = _batch_nouls(query, docs)
        return QueryResult(scores or [None] * len(docs), [call])


class JevChoice:
    key = "jev-choice"
    reverse = False

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        order = list(range(len(docs)))[::-1] if self.reverse else list(range(len(docs)))
        ids = [_pid(i) for i in order]                       # the id tells the model nothing about the original rank
        call, body = _ask(_state(query, [docs[i] for i in order], [f"p{k + 1:02d}" for k in range(len(order))]),
                          _choice_questions([f"p{k + 1:02d}" for k in range(len(order))]))
        if not body:
            return QueryResult([None] * len(docs), [call])
        best = body["answers"]["best"]
        probs = best["probabilities"]
        scores = [0.0] * len(docs)
        for k, i in enumerate(order):
            scores[i] = probs.get(f"p{k + 1:02d}", 0.0)
        return QueryResult(scores, [call], extra={"none_prob": probs.get("none", 0.0), "any_prob": body["answers"]["any"]["noul"],
                                                  "choice": best["choice"], "confidence": best.get("confidence"), "reversed": self.reverse})


class JevChoiceReversed(JevChoice):
    key = "jev-choice-reversed"
    reverse = True


class JevScoreBatch:
    key = "jev-score-batch"

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        questions = {_pid(i): {"type": "score", "instructions": f"How well does passage {_pid(i)} supply the information needed to answer or verify the query?",
                               "criteria": RUBRIC} for i in range(len(docs))}
        call, body = _ask(_state(query, docs), questions)
        if not body:
            return QueryResult([None] * len(docs), [call])
        scores, confs = [], []
        for i in range(len(docs)):
            a = body["answers"][_pid(i)]
            # Expected level from the distribution, scaled to 0..1 (0 = off-topic, 1 = fully supplies).
            legend = a.get("legend") or {}
            probs = a.get("probabilities") or {}
            if legend and probs:
                keys = sorted(legend, key=lambda k: RUBRIC.index(legend[k]) if legend[k] in RUBRIC else 0)
                ev = sum(probs.get(k, 0.0) * idx for idx, k in enumerate(keys)) / (len(keys) - 1)
            else:
                ev = float(a.get("score", 0.0))
            scores.append(ev)
            confs.append(a.get("confidence"))
        return QueryResult(scores, [call], extra={"confidence": confs})


class JevDuel:
    key = "jev-duel"
    TOP = 10

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        n = min(self.TOP, len(docs))
        ids = [_pid(i) for i in range(n)]
        questions = {}
        for a, b in combinations(ids, 2):
            questions[f"{a}_{b}"] = {"type": "choice",
                                     "instructions": f"Which of passages {a} and {b} better contains the information needed to answer or verify the query?",
                                     "criteria": {a: None, b: None}}
        call, body = _ask(_state(query, docs[:n], ids), questions)
        if not body:
            return QueryResult([None] * len(docs), [call])
        wins = {i: 0.0 for i in ids}
        for name, ans in body["answers"].items():
            a, b = name.split("_")
            pa = ans["probabilities"].get(a, 0.0)
            wins[a] += pa
            wins[b] += 1.0 - pa
        # Duelled passages score by expected wins (0..n-1); the rest keep BM25 order below them.
        scores = [wins[_pid(i)] for i in range(n)] + [-(i + 1) for i in range(n, len(docs))]
        return QueryResult(scores, [call], extra={"duels": len(questions), "wins": wins})


class JevTournament:
    key = "jev-tournament"
    GROUP = 5

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        ids = [_pid(i) for i in range(len(docs))]
        groups = [ids[g:g + self.GROUP] for g in range(0, len(ids), self.GROUP)]
        questions = {}
        for gi, g in enumerate(groups):
            crit = {i: None for i in g}
            crit["none"] = "None of these passages contains the information needed to answer or verify the query."
            questions[f"g{gi}"] = {"type": "choice",
                                   "instructions": f"Among passages {', '.join(g)}, which contains the information needed to answer or verify the query? Pick none if none does.",
                                   "criteria": crit}
        call1, body1 = _ask(_state(query, docs, ids), questions)
        if not body1:
            return QueryResult([None] * len(docs), [call1])
        group_prob = {}
        winners = []
        for gi, g in enumerate(groups):
            probs = body1["answers"][f"g{gi}"]["probabilities"]
            for i in g:
                group_prob[i] = probs.get(i, 0.0)
            winners.append(max(g, key=lambda i: group_prob[i]))
        wdocs = [docs[ids.index(w)] for w in winners]
        call2, body2 = _ask(_state(query, wdocs, winners), _choice_questions(winners))
        if not body2:
            return QueryResult([None] * len(docs), [call1, call2])
        final = body2["answers"]["best"]["probabilities"]
        scores = [1.0 + final.get(i, 0.0) if i in winners else group_prob[i] for i in ids]
        return QueryResult(scores, [call1, call2], extra={"none_prob": final.get("none", 0.0), "any_prob": body2["answers"]["any"]["noul"],
                                                          "winners": winners, "confidence": body2["answers"]["best"].get("confidence")})


class JevCascade:
    key = "jev-cascade"
    KEEP = 8

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        from rerankers import RELEVANCE_QUESTION
        call1, batch = _batch_nouls(query, docs)
        if batch is None:
            return QueryResult([None] * len(docs), [call1])
        keep = sorted(range(len(docs)), key=lambda i: -batch[i])[:self.KEEP]
        calls, scores = [call1], list(batch)
        for i in keep:
            call, body = _ask({"query": query, "passage": docs[i]}, {"relevant": _noul(RELEVANCE_QUESTION)})
            calls.append(call)
            if not body:
                return QueryResult([None] * len(docs), calls)
            scores[i] = 1.0 + body["answers"]["relevant"]["noul"]   # the re-judged 8 rank above the pruned 22
        return QueryResult(scores, calls, extra={"kept": [_pid(i) for i in keep]})
