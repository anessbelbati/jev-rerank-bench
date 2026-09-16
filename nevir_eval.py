"""Score the NevIR runs: paired accuracy, the benchmark's official metric.

A pair is two near-identical passages differing by a negation and two questions, one per passage. A model gets the
pair right only if it ranks passage 1 first for question 1 AND passage 2 first for question 2. A tie in scores counts
as wrong (a tie means the model did not see the negation). Random independent guessing scores 25%. Also reported:
per-question accuracy (50% random), and how often the two questions got the same top pick (the "ignored the negation"
signature). Writes results/nevir.json. Never mixed into the ranking averages.
"""
from __future__ import annotations

import json
import statistics
from collections import defaultdict

import numpy as np

from common import CACHE, CANDIDATES, RESULTS, read_jsonl, jsonl_exists
from eval import LABELS, MODELS


def main() -> dict:
    cands = {r["qid"]: r for r in read_jsonl(CANDIDATES / "nevir.jsonl")}
    pairs = defaultdict(dict)
    for q, r in cands.items():
        pairs[r["pair"]][q[-2:]] = r
    out = {}
    per_pair: dict[str, dict[str, bool]] = {}
    for m in MODELS:
        p = CACHE / m / "nevir.present.jsonl"
        if not jsonl_exists(p):
            continue
        rows = {r["qid"]: r for r in read_jsonl(p)}
        ok_pairs, per_q, same_pick, lat, cost = [], [], [], [], 0.0
        failed = 0
        pair_ok: dict[str, bool] = {}
        for pid, qs in pairs.items():
            if not all(k in qs and qs[k]["qid"] in rows and rows[qs[k]["qid"]]["ok"] for k in ("q1", "q2")):
                failed += 1
                continue
            picks = {}
            for k in ("q1", "q2"):
                r = rows[qs[k]["qid"]]
                s = dict(zip(r["dids"], r["scores"]))
                rel = next(iter(qs[k]["relevant"]))
                other = [d for d in r["dids"] if d != rel][0]
                right = s[rel] > s[other]             # strict: a tie is wrong
                per_q.append(right)
                picks[k] = max(r["dids"], key=lambda d: (s[d], -r["dids"].index(d)))
                lat.append(r["query_ms"]); cost += r["cost_usd"]
            ok_pairs.append(per_q[-2] and per_q[-1])
            pair_ok[pid] = ok_pairs[-1]
            same_pick.append(picks["q1"] == picks["q2"])
        if not ok_pairs:
            continue
        per_pair[m] = pair_ok
        out[m] = {"pairs": len(ok_pairs), "pairs_failed": failed, "paired_accuracy": statistics.mean(ok_pairs),
                  "question_accuracy": statistics.mean(per_q), "same_top_pick_share": statistics.mean(same_pick),
                  "query_ms_median": statistics.median(lat), "cost_usd": cost, "cost_per_1k_questions": cost / len(per_q) * 1000}
        o = out[m]
        print(f"{LABELS.get(m, m):45} pairs {o['pairs']:4} (failed {failed:3})  paired {o['paired_accuracy']:6.1%}  "
              f"per-question {o['question_accuracy']:6.1%}  same pick for both {o['same_top_pick_share']:6.1%}  {o['query_ms_median']:5.0f} ms  ${o['cost_per_1k_questions']:.3f}/1k")
    # Paired bootstrap over the pairs (10,000 resamples) for every complete model against the best complete model.
    complete = [m for m in per_pair if out[m]["pairs_failed"] == 0 and m != "bm25"]
    if len(complete) >= 2:
        B = 10_000
        pids = sorted(pairs)
        rng = np.random.default_rng(0)
        idx = rng.integers(0, len(pids), size=(B, len(pids)))
        arrs = {m: np.array([1.0 if per_pair[m][q] else 0.0 for q in pids]) for m in complete}
        boot = {m: arrs[m][idx].mean(axis=1) for m in complete}
        best = max(complete, key=lambda m: out[m]["paired_accuracy"])
        res = {}
        for a in complete:
            for b in complete:
                if a == b:
                    continue
                d = boot[a] - boot[b]
                lo, hi = np.percentile(d, [2.5, 97.5])
                pv = min(1.0, 2 * min(float((d <= 0).mean()), float((d >= 0).mean())))
                res[f"{a}|{b}"] = {"diff": float(arrs[a].mean() - arrs[b].mean()), "ci95": [float(lo), float(hi)], "p": pv, "real": bool(pv < 0.05), "B": B}
        out["_bootstrap"] = res
        for m in complete:
            if m != best:
                v = res[f"{best}|{m}"]
                print(f"   {best} vs {m:20} gap {100 * v['diff']:+.1f} points [{100 * v['ci95'][0]:+.1f}, {100 * v['ci95'][1]:+.1f}] p={v['p']:.3f} {'REAL' if v['real'] else 'within noise'}")
    return out


if __name__ == "__main__":
    res = main()
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "nevir.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("wrote", RESULTS / "nevir.json")
