"""What packing several queries into one Jev request does to the bill, the speed and the answers.

Jev bills the input tokens of a request: the state (passages) plus the question text. Output is free. So when several
queries share the same passages, one request with all their questions pays the passages once.

A. Billing curve: one fixed 30-passage state, K = 1, 2, 5, 10, 20, 40 queries' Choice questions in one request.
   Reads usage.input_tokens and the latency. Shows what one extra question costs.
B. Cross-talk: groups of K = 1, 2, 3, 4 SciFact queries; the state holds all their queries and the union of their BM25
   top-30 lists; each query gets its own Choice over its own 30 passage ids (+none). Scored exactly like jev-choice
   (nDCG@10, top-1) on the same queries and compared with the one-query-per-request baseline from cache/. K=1 is
   the control for the wording change ("query q1" instead of "the query").
Writes results/batching.json. SciFact only; costs about 20 cents.
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from datetime import datetime, timezone

from common import CANDIDATES, CACHE, RESULTS, read_jsonl, truncate
from eval import ndcg, order
from rerankers import RELEVANCE_FALSE, RELEVANCE_TRUE
from rerankers.jev import _ask

N = int(sys.argv[1]) if len(sys.argv) > 1 else 120
docs = {r["did"]: r["text"] for r in read_jsonl(CANDIDATES / "scifact.docs.jsonl")}
cands = [r for r in read_jsonl(CANDIDATES / "scifact.jsonl") if r["n_rel_top30"] > 0][:N]
baseline = {r["qid"]: r for r in read_jsonl(CACHE / "jev-choice" / "scifact.present.jsonl")}


def packed_questions(qkey: str, pids: list[str]) -> dict:
    criteria = {p: None for p in pids}
    criteria["none"] = f"No listed passage contains the information needed to answer or verify query {qkey}."
    return {
        f"best_{qkey}": {"type": "choice",
                         "instructions": f"Which passage contains the information needed to answer or verify query {qkey}? Pick none if no passage does.",
                         "criteria": criteria},
        f"any_{qkey}": {"type": "noul",
                        "instructions": f"Does any listed passage contain the information needed to answer or verify query {qkey}?",
                        "criteria": {"true": "At least one passage " + RELEVANCE_TRUE[len("The passage "):],
                                     "false": "Every passage " + RELEVANCE_FALSE[len("The passage "):]}},
    }


def pack(group: list[dict]):
    """State with K queries and the union of their candidate passages; one Choice + one any per query."""
    pid_of: dict[str, str] = {}
    passages: dict[str, str] = {}
    for r in group:
        for c in r["present"]:
            if c["did"] not in pid_of:
                pid_of[c["did"]] = f"p{len(pid_of) + 1:03d}"
                passages[pid_of[c["did"]]] = truncate(docs[c["did"]])
    queries = {f"q{i + 1}": r["query"] for i, r in enumerate(group)}
    questions = {}
    for i, r in enumerate(group):
        questions.update(packed_questions(f"q{i + 1}", [pid_of[c["did"]] for c in r["present"]]))
    return {"queries": queries, "passages": passages}, questions, pid_of


def billing_curve() -> list[dict]:
    out = []
    base = cands[0]
    for k in (1, 2, 5, 10, 20, 40):
        group = [dict(r, present=base["present"]) for r in cands[:k]]   # same 30 passages, k different queries
        state, questions, _ = pack(group)
        call, body = _ask(state, questions)
        row = {"k": k, "passages": len(state["passages"]), "status": call.status, "latency_ms": call.latency_ms,
               "input_tokens": call.usage.get("input_tokens"), "output_tokens": call.usage.get("output_tokens"), "cost_usd": call.cost_usd,
               "error": call.error}
        if body:   # does query 1's own answer move when other queries' questions ride along?
            q1 = body["answers"]["best_q1"]
            row["q1_choice"] = q1["choice"]; row["q1_top_prob"] = max(q1["probabilities"].values()); row["q1_none_prob"] = q1["probabilities"].get("none", 0.0)
        out.append(row)
        print(f"A k={k:2} passages={row['passages']} status={row['status']} input_tokens={row['input_tokens']} "
              f"latency={row['latency_ms']:.0f} ms cost=${row['cost_usd']:.6f} q1 -> {row.get('q1_choice')} p={row.get('q1_top_prob', 0):.2f}")
    return out


def crosstalk(k: int) -> dict:
    groups = [cands[i:i + k] for i in range(0, len(cands) - len(cands) % k, k)]
    per_q, calls = [], []
    for group in groups:
        state, questions, pid_of = pack(group)
        call, body = _ask(state, questions)
        calls.append({"status": call.status, "latency_ms": call.latency_ms, "input_tokens": call.usage.get("input_tokens"),
                      "cost_usd": call.cost_usd, "passages": len(state["passages"]), "error": call.error})
        if not body:
            print(f"B k={k} call failed: HTTP {call.status} {str(call.raw)[:200]}")
            continue
        for i, r in enumerate(group):
            probs = body["answers"][f"best_q{i + 1}"]["probabilities"]
            scores = [probs.get(pid_of[c["did"]], 0.0) for c in r["present"]]
            row = {"dids": [c["did"] for c in r["present"]], "scores": scores}
            b = baseline[r["qid"]]
            per_q.append({"qid": r["qid"], "ndcg10": ndcg(order(row), r["relevant"]), "top1": order(row)[0] in r["relevant"],
                          "base_ndcg10": ndcg(order(b), r["relevant"]), "base_top1": order(b)[0] in r["relevant"],
                          "same_top1": order(row)[0] == order(b)[0], "none_prob": probs.get("none", 0.0)})
    ok = [c for c in calls if c["status"] == 200]
    res = {"k": k, "groups": len(groups), "calls_ok": len(ok), "queries_scored": len(per_q),
           "ndcg10": statistics.mean(x["ndcg10"] for x in per_q) if per_q else None,
           "top1": statistics.mean(x["top1"] for x in per_q) if per_q else None,
           "baseline_ndcg10": statistics.mean(x["base_ndcg10"] for x in per_q) if per_q else None,
           "baseline_top1": statistics.mean(x["base_top1"] for x in per_q) if per_q else None,
           "same_top1_share": statistics.mean(x["same_top1"] for x in per_q) if per_q else None,
           "latency_ms_median": statistics.median(c["latency_ms"] for c in ok) if ok else None,
           "input_tokens_per_call": statistics.mean(c["input_tokens"] for c in ok) if ok else None,
           "cost_per_1k_queries": sum(c["cost_usd"] for c in ok) / len(per_q) * 1000 if per_q else None,
           "baseline_cost_per_1k_queries": sum(baseline[x["qid"]]["cost_usd"] for x in per_q) / len(per_q) * 1000 if per_q else None,
           "largest_ok_input_tokens": max((c["input_tokens"] for c in ok), default=None),
           "errors": [c for c in calls if c["status"] != 200]}
    if per_q:
        print(f"B k={k} queries={res['queries_scored']} nDCG {res['ndcg10']:.3f} (baseline {res['baseline_ndcg10']:.3f}) "
              f"top1 {res['top1']:.3f} (baseline {res['baseline_top1']:.3f}) same top1 {res['same_top1_share']:.0%} | "
              f"{res['latency_ms_median']:.0f} ms per call, {res['input_tokens_per_call']:.0f} tokens per call, "
              f"${res['cost_per_1k_queries']:.3f}/1k (baseline ${res['baseline_cost_per_1k_queries']:.3f})")
    else:
        print(f"B k={k}: nothing scored")
    return res


if __name__ == "__main__":
    t0 = time.time()
    res = {"measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "dataset": "scifact", "queries": len(cands),
           "billing_curve": billing_curve(), "crosstalk": [crosstalk(k) for k in (1, 2, 3, 4)]}
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "batching.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print(f"wrote {RESULTS / 'batching.json'} in {time.time() - t0:.0f}s")
