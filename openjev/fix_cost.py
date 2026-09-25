"""Halve the saved cost of the Open-Jev runs of 2026-09-22. Each server copy had two questions in flight (one run.py
shard with --workers 2 per copy), so charging every call its wall time at the pod price divided by the copies counted
each second of card time twice; the right divisor is copies x 2. Only the cost fields change (the row's and each
call's); responses, scores and timings stay as saved. Each corrected row carries extra.cost_note, and a second run
changes nothing.

    uv run openjev/fix_cost.py            # what it would change
    uv run openjev/fix_cost.py --write
"""
import gzip, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
NOTE = ("cost halved 2026-09-25: two questions were in flight on each server copy, and the first charge divided the "
        "pod price by the server copies only")

for key in ("open-jev-2b-noul-pair", "open-jev-9b-noul-pair"):
    before = after = 0.0
    changed = 0
    for p in sorted((ROOT / "cache" / key).glob("*.jsonl.gz")):
        with gzip.open(p, "rt", encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
        for r in rows:
            before += r["cost_usd"]
            if (r.get("extra") or {}).get("cost_note") != NOTE:
                assert r.get("workers") == 2, (p.name, r["qid"], r.get("workers"))
                r["cost_usd"] /= 2
                for c in r["calls"]:
                    if c.get("cost_usd") is not None:
                        c["cost_usd"] /= 2
                r["extra"] = {**(r.get("extra") or {}), "cost_note": NOTE}
                changed += 1
            after += r["cost_usd"]
        if "--write" in sys.argv:
            with gzip.open(p, "wt", encoding="utf-8") as f:
                for r in rows:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{key}: {changed} rows halved; saved cost of every row ${before:.2f} -> ${after:.2f}"
          + ("" if "--write" in sys.argv else "  (dry run: --write saves)"))
