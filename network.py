"""How much of the measured latency is the trip from Algeria, and how much is the model.

1. TCP connect time to each API host (about one network round trip), IPv4, 7 samples.
2. Real 30-passage Jev calls on SciFact (N queries per mode): our HTTP round trip vs Jev's own server-side time, which
   the API returns in the `x-envoy-upstream-service-time` header (Cohere via OpenRouter and ZeroEntropy return no such
   header, so for them the model-only time can only be estimated as round trip minus the same trip).
Writes results/network.json. Costs a few cents.
"""
from __future__ import annotations

import json
import socket
import statistics
import sys
import time
from datetime import datetime, timezone

import common
from common import CANDIDATES, RESULTS, read_jsonl, truncate
import rerankers.jev as J

HOSTS = {"api.typesafe.ai": "Jev", "openrouter.ai": "OpenRouter (Cohere, DeepSeek)", "api.zeroentropy.dev": "ZeroEntropy"}
MODES = {"jev-score-batch": J.JevScoreBatch, "jev-noul-batch": J.JevNoulBatch, "jev-choice": J.JevChoice}


def connect_times() -> dict:
    out = {}
    for host, label in HOSTS.items():
        ip = socket.getaddrinfo(host, 443, socket.AF_INET)[0][4][0]
        ms = []
        for _ in range(7):
            t = time.perf_counter()
            s = socket.create_connection((ip, 443), timeout=10)
            ms.append((time.perf_counter() - t) * 1000)
            s.close()
        out[host] = {"label": label, "median_ms": statistics.median(ms), "min_ms": min(ms), "samples": len(ms)}
        print(f"{label:30} TCP connect: median {out[host]['median_ms']:.0f} ms, min {out[host]['min_ms']:.0f} ms")
    return out


def jev_server_time(n: int) -> dict:
    rec: list[tuple[float, float, int, int]] = []
    orig = common.post_json

    def patched(url, headers, body, **kw):
        status, parsed, ms, hdrs = orig(url, headers, body, **kw)
        rec.append((ms, float(hdrs.get("x-envoy-upstream-service-time", "nan")), status, len(json.dumps(body).encode("utf-8")),
                    len(json.dumps(parsed).encode("utf-8")) if not isinstance(parsed, str) else len(parsed)))
        return status, parsed, ms, hdrs

    J.post_json = patched
    docs = {r["did"]: r["text"] for r in read_jsonl(CANDIDATES / "scifact.docs.jsonl")}
    rows = read_jsonl(CANDIDATES / "scifact.jsonl")[:n]
    out = {}
    for key, cls in MODES.items():
        rec.clear()
        rr = cls()
        for r in rows:
            rr.rerank(r["query"], [truncate(docs[c["did"]]) for c in r["present"]], bm25=[c["bm25"] for c in r["present"]])
        ok = [x for x in rec if x[2] == 200 and x[1] == x[1]]
        out[key] = {"n": len(ok), "round_trip_ms_median": statistics.median(x[0] for x in ok),
                    "server_ms_median": statistics.median(x[1] for x in ok), "request_kb_median": statistics.median(x[3] for x in ok) / 1024,
                    "response_kb_median": statistics.median(x[4] for x in ok) / 1024}
        o = out[key]
        print(f"{key:16} n={o['n']} round trip {o['round_trip_ms_median']:.0f} ms | Jev server time {o['server_ms_median']:.0f} ms | "
              f"trip {o['round_trip_ms_median'] - o['server_ms_median']:.0f} ms | request {o['request_kb_median']:.0f} KB | response {o['response_kb_median']:.0f} KB")
    return out


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    res = {"measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "from": "Algiers, home connection",
           "tcp_connect": connect_times(), "jev_server_time": jev_server_time(n)}
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "network.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("wrote", RESULTS / "network.json")
