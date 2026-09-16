"""Cold start: how long does Jev's first call take after the API has been idle for a while?

Sends one small yes/no request, then waits the given number of seconds with no traffic, then sends again, and records
the wall-clock time of each. Each probe uses a fresh connection so connection reuse cannot hide a server-side stall.
Writes results/coldstart.json. Run when nothing else is calling Jev from this key.
"""
from __future__ import annotations

import json
import sys
import time

import requests

from common import RESULTS, env

URL = "https://api.typesafe.ai/v1/systemone"
BODY = {"state": {"query": "capital of France?", "passage": "Paris is the capital of France."}, "model": "jev-latest",
        "questions": {"r": {"type": "noul", "instructions": "Does the passage answer the query?"}}}
GAPS = [int(x) for x in sys.argv[1:]] or [60, 120, 300, 600, 900]


def one() -> float:
    s = requests.Session()
    t = time.perf_counter()
    r = s.post(URL, headers={"Authorization": f"Bearer {env('JEV_API_KEY')}", "Content-Type": "application/json"}, json=BODY, timeout=120)
    ms = (time.perf_counter() - t) * 1000
    r.raise_for_status()
    return ms


rows = []
warm = [one() for _ in range(3)]
rows.append({"idle_s": 0, "first_call_ms": warm[0], "next_two_ms": warm[1:]})
for gap in GAPS:
    time.sleep(gap)
    first = one()
    after = [one() for _ in range(2)]
    rows.append({"idle_s": gap, "first_call_ms": first, "next_two_ms": after})
    (RESULTS / "coldstart.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    print(f"idle {gap:4d}s -> first call {first:7.0f} ms, then {after[0]:.0f} / {after[1]:.0f} ms", flush=True)
