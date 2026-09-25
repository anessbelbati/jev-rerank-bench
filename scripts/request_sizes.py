"""How big each Jev setup's requests get on this benchmark: passages per request and input tokens.

    uv run scripts/request_sizes.py        # writes results/request_sizes.json (read by rerankers/registry.py)

Tokens are Jev's own count (usage.input_tokens of every saved call), over all 14 datasets and NevIR, both variants.
Tournament and cascade are measured on their first call, the one that holds all 30 passages. choice-reversed sends
choice's passages and questions in reverse order, so it takes choice's sizes; score-pair (the rubric one passage per
request) takes noul-pair's, the same state with one question. Another model's tokenizer counts somewhat differently.
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import CACHE, DATASETS, EXTRA, RESULTS, read_jsonl  # noqa: E402

PASSAGES = {"noul-pair": 1, "noul-batch": 30, "choice": 30, "score-batch": 30, "duel": 10, "tournament": 30, "cascade": 30}
FIRST_CALL_ONLY = {"tournament", "cascade"}
SAME_AS = {"choice-reversed": "choice", "score-pair": "noul-pair"}


def measure(mode: str) -> dict:
    toks = []
    for ds in DATASETS + EXTRA:
        for variant in ("present", "absent"):
            for row in read_jsonl(CACHE / f"jev-{mode}" / f"{ds}.{variant}.jsonl"):
                if row["ok"]:
                    calls = row["calls"][:1] if mode in FIRST_CALL_ONLY else row["calls"]
                    toks += [c["usage"]["input_tokens"] for c in calls if c["status"] == 200]
    toks.sort()
    return {"passages": PASSAGES[mode], "max_input_tokens": toks[-1], "p99_input_tokens": toks[int(0.99 * (len(toks) - 1))],
            "median_input_tokens": statistics.median(toks), "calls": len(toks)}


if __name__ == "__main__":
    modes = {m: measure(m) for m in PASSAGES}
    for m, src in SAME_AS.items():
        modes[m] = {**modes[src], "same_as": src}
    out = {"source": "usage.input_tokens of every saved Jev call (cache/jev-*), all 14 datasets and NevIR, both variants",
           "modes": modes}
    (RESULTS / "request_sizes.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    print(f"{'mode':16} {'passages':>8} {'max tokens':>11} {'p99':>7} {'median':>7} {'calls':>8}")
    for m, s in modes.items():
        print(f"{m:16} {s['passages']:8} {s['max_input_tokens']:11,} {s['p99_input_tokens']:7,} {s['median_input_tokens']:7,.0f} "
              f"{s['calls']:8,}" + (f"   (= {s['same_as']})" if "same_as" in s else ""))
