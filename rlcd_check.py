"""Does the Qwen RLCD recipe's score carry signal, and does it drift with passage position?

Pools the 8 headline English datasets (present lists only). For each model: mean score of relevant vs non-relevant
passages, and the mean score at positions 1, 15 and 30 of the list (a flat model shows the same mean everywhere).
Jev's yes/no batch mode is the comparison because it has the same wording and the same 30 passages in one call.
Writes results/rlcd_check.json.
"""
from __future__ import annotations

import json
import statistics

from common import CACHE, CANDIDATES, ENGLISH, RESULTS, read_jsonl, jsonl_exists

MODELS = ("qwen-rlcd-batch", "qwen-rlcd-rubric", "qwen-rlcd-pair", "jev-noul-batch", "jev-score-batch", "jev-noul-pair")


def main() -> dict:
    out = {}
    for m in MODELS:
        rel_s, non_s, pos = [], [], {1: [], 15: [], 30: []}
        for ds in ENGLISH:
            p = CACHE / m / f"{ds}.present.jsonl"
            if not jsonl_exists(p):
                continue
            cands = {r["qid"]: set(r["relevant"]) for r in read_jsonl(CANDIDATES / f"{ds}.jsonl")}
            for r in read_jsonl(p):
                if not r["ok"] or r["qid"] not in cands:
                    continue
                for i, (d, s) in enumerate(zip(r["dids"], r["scores"]), 1):
                    (rel_s if d in cands[r["qid"]] else non_s).append(s)
                    if i in pos:
                        pos[i].append(s)
        if not rel_s:
            continue
        out[m] = {"relevant_mean": statistics.mean(rel_s), "non_relevant_mean": statistics.mean(non_s),
                  "gap": statistics.mean(rel_s) - statistics.mean(non_s),
                  "position_mean": {str(k): statistics.mean(v) for k, v in pos.items()},
                  "n_relevant": len(rel_s), "n_non_relevant": len(non_s)}
        o = out[m]
        print(f"{m:16} relevant {o['relevant_mean']:.3f}  non-relevant {o['non_relevant_mean']:.3f}  gap {o['gap']:+.3f}  "
              f"position 1/15/30: {o['position_mean']['1']:.3f} / {o['position_mean']['15']:.3f} / {o['position_mean']['30']:.3f}")
    return out


if __name__ == "__main__":
    res = main()
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "rlcd_check.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("wrote", RESULTS / "rlcd_check.json")
