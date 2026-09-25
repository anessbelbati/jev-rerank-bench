"""Any server that speaks TypeSafe's System One protocol, asked the eight ways rerankers/jev.py asks Jev.

A copy of jev.py with the host, model, key and price as settings (an Endpoint) instead of fixed values, so the same
requests can go to Jev, to Jev through OpenRouter, or to an open-weight rebuild on a rented GPU. The questions, the
criteria and the state layout are byte for byte those of jev.py; scripts/validate_systemone.py checks that against
the saved Jev responses behind the headline (eight English datasets, both variants, and NevIR).

The protocol, as used here: POST <base_url>/systemone with {"state": ..., "model": ..., "questions": {name: question}}.
A question is {"type": "noul" | "choice" | "score", "instructions": str, "criteria": ...}. The reply carries
{"answers": {name: answer}, "usage": {...}}: a noul answer holds "noul" (P(true)); a choice answer holds "choice",
"probabilities" over the criteria keys and "confidence"; a score answer holds "legend" (level -> criterion text),
"probabilities" over the levels, "score" and "confidence".

Modes (the jev.py class each one copies):
- noul-pair       JevNoulPair: one call per (query, passage), one yes/no question.
- noul-batch      JevNoulBatch: one call per query, 30 passages in the state, 30 yes/no questions.
- choice          JevChoice: one Choice over the passage ids plus "none", and a yes/no "does any passage answer it".
- choice-reversed JevChoiceReversed: choice with the passages sent in reverse order.
- score-batch     JevScoreBatch: 30 Score questions with a four-level rubric in one call.
- duel            JevDuel: all 45 pairwise Choices over the top 10 in one call.
- tournament      JevTournament: six Choices over groups of five, then a final Choice among the winners.
- cascade         JevCascade: one batched yes/no call prunes 30 to 8, then per-pair yes/no on the 8.
- score-pair      not in jev.py: the four-level rubric one passage per request, worded as laya-score-pair was asked
                  (small_models_runner.py). The one-passage form of score-batch, for servers that cannot take 30.
Only noul-pair and score-pair send one passage per request; the others need a server whose window holds all the
passages at once (rerankers/registry.py falls back to the one-passage forms when it cannot).
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from common import Call, QueryResult, env, post_json

RUBRIC = ["The passage is off-topic for the query.",
          "The passage is on a related topic but does not supply what the query asks for.",
          "The passage partly supplies the information needed to answer or verify the query.",
          "The passage fully supplies the information needed to answer or verify the query."]
# The rubric question for one passage per request: score-batch's question with "passage pNN" as "the passage", the
# same words laya-score-pair got (small_models_runner.py SCORE_QUESTION).
SCORE_QUESTION = "How well does the passage supply the information needed to answer or verify the query?"


@dataclass(frozen=True)
class Endpoint:
    """Where to send the requests and how to price them.

    base_url: up to the version, e.g. https://api.typesafe.ai/v1 (Jev), https://openrouter.ai/api/v1 (Jev through
    OpenRouter), http://127.0.0.1:8791/v1 (a local server); /systemone is added unless it is already there.
    key_env: the name of the environment variable (or .env entry) holding the bearer key; None sends no key.
    Cost of a call, first that applies: gpu_usd_per_hour (self-hosted: the card's hourly price divided by the server
    copies sharing it, times the call's wall time); the reply's usage.cost (OpenRouter bills each call and says how
    much); input tokens x input_per_m + output tokens x output_per_m, USD per million.
    """
    base_url: str
    model: str
    key_env: str | None = None
    input_per_m: float = 0.0
    output_per_m: float = 0.0
    gpu_usd_per_hour: float | None = None

    @property
    def url(self) -> str:
        base = self.base_url.rstrip("/")
        return base if base.endswith("/systemone") else base + "/systemone"

    def headers(self) -> dict:
        h = {"Content-Type": "application/json", "Accept": "application/json"}
        if self.key_env:
            h = {"Authorization": f"Bearer {env(self.key_env)}", **h}
        return h

    def cost(self, usage: dict, ms: float) -> float:
        if self.gpu_usd_per_hour is not None:
            return ms / 3.6e6 * self.gpu_usd_per_hour
        if "cost" in usage:
            return float(usage["cost"] or 0.0)
        return usage.get("input_tokens", 0) * self.input_per_m / 1e6 + usage.get("output_tokens", 0) * self.output_per_m / 1e6


def _ask(ep: Endpoint, state, questions: dict) -> tuple[Call, dict | None]:
    status, body, ms, _ = post_json(ep.url, ep.headers(), {"state": state, "model": ep.model, "questions": questions})
    if status != 200 or not isinstance(body, dict):
        return Call(ms, status, {}, 0.0, raw=body if isinstance(body, dict) else str(body)[:500], error=f"HTTP {status}"), None
    usage = body.get("usage") or {}
    problem = _unreadable(questions, body)
    if problem:     # the call happened and is billed, but the question counts as failed instead of stopping the run
        return Call(ms, status, usage, ep.cost(usage, ms), raw=body, error=problem), None
    return Call(ms, status, usage, ep.cost(usage, ms), raw=body), body


def _number(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _unreadable(questions: dict, body: dict) -> str | None:
    """Why a 200 reply cannot be read as the answers to these questions, or None when it can."""
    answers = body.get("answers")
    if not isinstance(answers, dict):
        return "the reply has no 'answers' object"
    for name, q in questions.items():
        a = answers.get(name)
        if not isinstance(a, dict):
            return f"no answer for question {name!r}"
        probs = a.get("probabilities")
        probs_ok = isinstance(probs, dict) and all(_number(v) for v in probs.values())
        if q["type"] == "noul" and not _number(a.get("noul")):
            return f"answer {name!r}: 'noul' must be a number (the probability of true)"
        if q["type"] == "choice" and not probs_ok:
            return f"answer {name!r}: 'probabilities' must give a number for each option"
        if q["type"] == "score":
            legend = a.get("legend")
            if isinstance(legend, dict) and legend:
                if not probs_ok or not set(legend.values()) <= set(q["criteria"]):
                    return (f"answer {name!r}: 'legend' must name each level by the criterion text it was sent, "
                            f"with a number per level in 'probabilities'")
            elif not _number(a.get("score")):
                return f"answer {name!r}: needs 'legend' and 'probabilities', or a 'score' from 0 to 1"
    return None


def _noul(instructions: str) -> dict:
    from rerankers import RELEVANCE_FALSE, RELEVANCE_TRUE
    return {"type": "noul", "instructions": instructions, "criteria": {"true": RELEVANCE_TRUE, "false": RELEVANCE_FALSE}}


def _pid(i: int) -> str:
    return f"p{i + 1:02d}"


def _state(query: str, docs: list[str], ids: list[str] | None = None) -> dict:
    ids = ids or [_pid(i) for i in range(len(docs))]
    return {"query": query, "passages": dict(zip(ids, docs))}


def _choice_questions(ids: list[str]) -> dict:
    """The Choice + any-noul pair used by choice, tournament and choice-reversed."""
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


class _Mode:
    mode = ""

    def __init__(self, ep: Endpoint, key: str | None = None):
        self.ep = ep
        self.key = key or self.mode


class NoulPair(_Mode):
    mode = "noul-pair"

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        from rerankers import RELEVANCE_QUESTION
        scores, calls = [], []
        for d in docs:
            call, body = _ask(self.ep, {"query": query, "passage": d}, {"relevant": _noul(RELEVANCE_QUESTION)})
            calls.append(call)
            scores.append(body["answers"]["relevant"]["noul"] if body else None)
        return QueryResult(scores, calls)


def _batch_nouls(ep: Endpoint, query: str, docs: list[str]) -> tuple[Call, list[float] | None]:
    from rerankers import RELEVANCE_QUESTION
    questions = {_pid(i): _noul(RELEVANCE_QUESTION.replace("the passage", f"passage {_pid(i)}")) for i in range(len(docs))}
    call, body = _ask(ep, _state(query, docs), questions)
    return call, ([body["answers"][_pid(i)]["noul"] for i in range(len(docs))] if body else None)


class NoulBatch(_Mode):
    mode = "noul-batch"

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        call, scores = _batch_nouls(self.ep, query, docs)
        return QueryResult(scores or [None] * len(docs), [call])


class Choice(_Mode):
    mode = "choice"
    reverse = False

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        order = list(range(len(docs)))[::-1] if self.reverse else list(range(len(docs)))
        call, body = _ask(self.ep, _state(query, [docs[i] for i in order], [f"p{k + 1:02d}" for k in range(len(order))]),
                          _choice_questions([f"p{k + 1:02d}" for k in range(len(order))]))
        if not body:
            return QueryResult([None] * len(docs), [call])
        best = body["answers"]["best"]
        probs = best["probabilities"]
        scores = [0.0] * len(docs)
        for k, i in enumerate(order):
            scores[i] = probs.get(f"p{k + 1:02d}", 0.0)
        return QueryResult(scores, [call], extra={"none_prob": probs.get("none", 0.0), "any_prob": body["answers"]["any"]["noul"],
                                                  "choice": best.get("choice"), "confidence": best.get("confidence"), "reversed": self.reverse})


class ChoiceReversed(Choice):
    mode = "choice-reversed"
    reverse = True


class ScoreBatch(_Mode):
    mode = "score-batch"

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        questions = {_pid(i): {"type": "score", "instructions": f"How well does passage {_pid(i)} supply the information needed to answer or verify the query?",
                               "criteria": RUBRIC} for i in range(len(docs))}
        call, body = _ask(self.ep, _state(query, docs), questions)
        if not body:
            return QueryResult([None] * len(docs), [call])
        answers = [body["answers"][_pid(i)] for i in range(len(docs))]
        return QueryResult([_expected_level(a) for a in answers], [call], extra={"confidence": [a.get("confidence") for a in answers]})


def _expected_level(a: dict) -> float:
    """Expected rubric level from the distribution, scaled to 0..1 (0 = off-topic, 1 = fully supplies)."""
    legend = a.get("legend") or {}
    probs = a.get("probabilities") or {}
    if legend and probs:
        keys = sorted(legend, key=lambda k: RUBRIC.index(legend[k]) if legend[k] in RUBRIC else 0)
        return sum(probs.get(k, 0.0) * idx for idx, k in enumerate(keys)) / (len(keys) - 1)
    return float(a.get("score", 0.0))


class ScorePair(_Mode):
    mode = "score-pair"

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        scores, confs, calls = [], [], []
        for d in docs:
            call, body = _ask(self.ep, {"query": query, "passage": d},
                              {"relevant": {"type": "score", "instructions": SCORE_QUESTION, "criteria": RUBRIC}})
            calls.append(call)
            answer = body["answers"]["relevant"] if body else None
            scores.append(_expected_level(answer) if answer else None)
            confs.append(answer.get("confidence") if answer else None)
        return QueryResult(scores, calls, extra={"confidence": confs})


class Duel(_Mode):
    mode = "duel"
    TOP = 10

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        n = min(self.TOP, len(docs))
        ids = [_pid(i) for i in range(n)]
        questions = {}
        for a, b in combinations(ids, 2):
            questions[f"{a}_{b}"] = {"type": "choice",
                                     "instructions": f"Which of passages {a} and {b} better contains the information needed to answer or verify the query?",
                                     "criteria": {a: None, b: None}}
        call, body = _ask(self.ep, _state(query, docs[:n], ids), questions)
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


class Tournament(_Mode):
    mode = "tournament"
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
        call1, body1 = _ask(self.ep, _state(query, docs, ids), questions)
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
        call2, body2 = _ask(self.ep, _state(query, wdocs, winners), _choice_questions(winners))
        if not body2:
            return QueryResult([None] * len(docs), [call1, call2])
        final = body2["answers"]["best"]["probabilities"]
        scores = [1.0 + final.get(i, 0.0) if i in winners else group_prob[i] for i in ids]
        return QueryResult(scores, [call1, call2], extra={"none_prob": final.get("none", 0.0), "any_prob": body2["answers"]["any"]["noul"],
                                                          "winners": winners, "confidence": body2["answers"]["best"].get("confidence")})


class Cascade(_Mode):
    mode = "cascade"
    KEEP = 8

    def rerank(self, query: str, docs: list[str], **_) -> QueryResult:
        from rerankers import RELEVANCE_QUESTION
        call1, batch = _batch_nouls(self.ep, query, docs)
        if batch is None:
            return QueryResult([None] * len(docs), [call1])
        keep = sorted(range(len(docs)), key=lambda i: -batch[i])[:self.KEEP]
        calls, scores = [call1], list(batch)
        for i in keep:
            call, body = _ask(self.ep, {"query": query, "passage": docs[i]}, {"relevant": _noul(RELEVANCE_QUESTION)})
            calls.append(call)
            if not body:
                return QueryResult([None] * len(docs), calls)
            scores[i] = 1.0 + body["answers"]["relevant"]["noul"]   # the re-judged 8 rank above the pruned 22
        return QueryResult(scores, calls, extra={"kept": [_pid(i) for i in keep]})


MODES = {c.mode: c for c in (NoulPair, NoulBatch, Choice, ChoiceReversed, ScoreBatch, Duel, Tournament, Cascade, ScorePair)}


def make(ep: Endpoint, mode: str, key: str | None = None) -> _Mode:
    """The reranker for one mode on one endpoint; key names its cache folder (default: the mode)."""
    if mode not in MODES:
        raise SystemExit(f"unknown System One mode {mode!r}; known: {', '.join(MODES)}")
    return MODES[mode](ep, key)
