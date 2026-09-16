"""Does Jev move? The same request sent again should return the same distribution if the model is what it claims.

Takes the first N scored SciFact queries, re-sends the exact batched-yes/no and Choice requests twice, and compares
every probability with the cached first run. Writes results/determinism.json. Cost: N x 4 calls.
"""
from __future__ import annotations

import json
import statistics
import sys

from common import CANDIDATES, RESULTS, Cache, read_jsonl, truncate
from rerankers import REGISTRY

N = int(sys.argv[1]) if len(sys.argv) > 1 else 100


def compare(model_key: str) -> dict:
    rows = [r for r in read_jsonl(CANDIDATES / "scifact.jsonl") if r["n_rel_top30"] > 0][:N]
    docs = {r["did"]: r["text"] for r in read_jsonl(CANDIDATES / "scifact.docs.jsonl")}
    first = Cache(model_key, "scifact", "present").rows
    reranker = REGISTRY[model_key]()
    max_diffs, top1_changed, none_diffs, runs = [], 0, [], []
    for r in rows:
        base = first.get(r["qid"])
        if not base or not base["ok"]:
            continue
        texts = [truncate(docs[c["did"]]) for c in r["present"]]
        reps = [reranker.rerank(r["query"], texts) for _ in range(2)]
        for rep in reps:
            if not rep.ok:
                continue
            max_diffs.append(max(abs(a - b) for a, b in zip(base["scores"], rep.scores)))
            if max(range(len(texts)), key=lambda i: base["scores"][i]) != max(range(len(texts)), key=lambda i: rep.scores[i]):
                top1_changed += 1
            if "none_prob" in base["extra"]:
                none_diffs.append(abs(base["extra"]["none_prob"] - rep.extra["none_prob"]))
            runs.append({"qid": r["qid"], "scores": rep.scores, "extra": rep.extra, "cost_usd": rep.cost_usd})
    return {"model": model_key, "queries": len(rows), "repeats_per_query": 2, "comparisons": len(max_diffs),
            "max_abs_prob_diff_mean": statistics.mean(max_diffs) if max_diffs else None,
            "max_abs_prob_diff_max": max(max_diffs) if max_diffs else None,
            "identical_share": sum(1 for d in max_diffs if d == 0) / len(max_diffs) if max_diffs else None,
            "top1_changed": top1_changed, "none_prob_diff_max": max(none_diffs) if none_diffs else None,
            "cost_usd": sum(x["cost_usd"] for x in runs), "runs": runs}


if __name__ == "__main__":
    out = {m: compare(m) for m in ("jev-noul-batch", "jev-choice")}
    (RESULTS / "determinism.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for m, r in out.items():
        print(f"{m}: {r['comparisons']} repeats over {r['queries']} queries; identical {r['identical_share']:.0%}; "
              f"mean max-diff {r['max_abs_prob_diff_mean']:.3f}, worst {r['max_abs_prob_diff_max']:.3f}; top-1 changed {r['top1_changed']}x; "
              f"P(none) worst diff {r['none_prob_diff_max']}; ${r['cost_usd']:.4f}")
