"""Run one reranker over one dataset (both candidate variants by default), caching every raw response.

    uv run run.py --model jev-noul-batch --dataset scifact
    uv run run.py --model llm-gpt4o-mini --dataset all --workers 8
    uv run run.py --model cohere-pro --dataset fiqa --variant present --limit 20

A query already in the cache is skipped, so a crashed or rate-limited run just resumes. Latency is recorded per
HTTP call; `--workers` queries run at once, which is stated with the results.
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict

from tqdm import tqdm

from common import CANDIDATES, DATASETS, EXTRA, RESULTS, VARIANTS, Cache, read_jsonl, truncate
from rerankers import REGISTRY


def run(model_key: str, dataset: str, variant: str, limit: int | None, workers: int) -> dict:
    reranker = REGISTRY[model_key]()
    rows = read_jsonl(CANDIDATES / f"{dataset}.jsonl")
    docs = {r["did"]: r["text"] for r in read_jsonl(CANDIDATES / f"{dataset}.docs.jsonl")}
    cache = Cache(model_key, dataset, variant)
    # A query is redone only if it is missing or its last attempt failed (a rerun repairs, it never re-spends on successes).
    todo = [r for r in rows if r[variant] and not (cache.has(r["qid"]) and cache.rows[r["qid"]]["ok"])]
    if limit:
        todo = todo[:limit]

    def one(r: dict) -> dict:
        cands = r[variant]
        texts = [truncate(docs[c["did"]]) for c in cands]
        t0 = time.perf_counter()
        res = reranker.rerank(r["query"], texts, bm25=[c["bm25"] for c in cands])
        return {
            "qid": r["qid"], "variant": variant, "model": model_key, "dids": [c["did"] for c in cands],
            "scores": res.scores, "extra": res.extra, "ok": res.ok, "cost_usd": res.cost_usd,
            "query_ms": (time.perf_counter() - t0) * 1000,
            "calls": [asdict(c) for c in res.calls], "workers": workers, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

    done = 0
    with ThreadPoolExecutor(max_workers=workers) as pool, tqdm(total=len(todo), desc=f"{model_key} {dataset} {variant}", unit="q") as bar:
        futures = [pool.submit(one, r) for r in todo]
        for f in as_completed(futures):
            cache.put(f.result())
            done += 1
            bar.update(1)

    all_rows = [cache.rows[r["qid"]] for r in rows if r[variant] and cache.has(r["qid"])]
    lat = [c["latency_ms"] for row in all_rows for c in row["calls"] if c["status"] == 200]
    summary = {
        "model": model_key, "dataset": dataset, "variant": variant, "queries": len(all_rows), "new_this_run": done,
        "failed_queries": sum(1 for r in all_rows if not r["ok"]),
        "calls": sum(len(r["calls"]) for r in all_rows), "cost_usd": round(sum(r["cost_usd"] for r in all_rows), 6),
        "call_latency_ms_median": round(statistics.median(lat), 1) if lat else None,
        "call_latency_ms_p95": round(sorted(lat)[int(0.95 * (len(lat) - 1))], 1) if lat else None,
        "workers": workers, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    RESULTS.mkdir(exist_ok=True)
    with (RESULTS / "runs.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(summary) + "\n")
    print(json.dumps(summary))
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, choices=sorted(REGISTRY))
    ap.add_argument("--dataset", required=True, choices=list(DATASETS) + list(EXTRA) + ["all"])
    ap.add_argument("--variant", default="both", choices=list(VARIANTS) + ["both"])
    ap.add_argument("--limit", type=int, default=None, help="only this many uncached queries (smoke test)")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    for ds in (DATASETS if a.dataset == "all" else [a.dataset]):
        for v in (VARIANTS if a.variant == "both" else [a.variant]):
            run(a.model, ds, v, a.limit, a.workers)
