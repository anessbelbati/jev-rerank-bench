"""Run one reranker over one dataset (both candidate variants by default), caching every raw response.

    uv run run.py --model jev-noul-batch --dataset scifact
    uv run run.py --model llm-gpt4o-mini --dataset all --workers 8
    uv run run.py --model cohere-pro --dataset fiqa --variant present --limit 20
    uv run run.py --model open-jev-2b --dataset all      # a models.yaml entry: each of its modes, with its concurrency

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

from common import CANDIDATES, DATASETS, EXTRA, FOLLOWUP_VARIANTS, INJECT, INJECT_VARIANTS, RESULTS, VARIANTS, Cache, read_jsonl, truncate
from rerankers import KEY_ENTRY, MODELS, REGISTRY
from rerankers.registry import describe


def run(model_key: str, dataset: str, variant: str, limit: int | None, workers: int, cache_as: str | None = None, shard: str = "0/1", reverse: bool = False, slice_: str = "0/1", skip_file: str | None = None) -> dict:
    reranker = REGISTRY[model_key]()
    k, n = (int(x) for x in shard.split("/"))
    rows = read_jsonl(CANDIDATES / f"{dataset}.jsonl")[k::n]
    i, m = (int(x) for x in slice_.split("/"))
    rows = rows[i * len(rows) // m:(i + 1) * len(rows) // m]     # a fixed contiguous chunk of the shard, cut before the cache is consulted
    model_key = cache_as or model_key      # --cache-as: same setup, another backend (e.g. Open-Jev), its own cache folder
    docs = {r["did"]: r["text"] for r in read_jsonl(CANDIDATES / f"{dataset}.docs.jsonl")}
    cache = Cache(model_key, dataset, variant)
    # A query is redone only if it is missing or its last attempt failed (a rerun repairs, it never re-spends on successes).
    skip = set()
    if skip_file:       # "dataset|variant|qid" lines: rows another machine has already finished
        skip = {l.strip() for l in open(skip_file, encoding="utf-8") if l.strip()}
    todo = [r for r in rows if r[variant] and not (cache.has(r["qid"]) and cache.rows[r["qid"]]["ok"]) and f"{dataset}|{variant}|{r['qid']}" not in skip]
    if limit:
        todo = todo[:limit]
    if reverse:
        todo = todo[::-1]       # a helper pod walks the same shard from the other end; the merge keeps one row per qid

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
    ap.add_argument("--model", required=True, choices=sorted(REGISTRY) + sorted(MODELS),
                    help="a model key, or a models.yaml entry name (runs each of its modes)")
    ap.add_argument("--dataset", choices=list(DATASETS) + list(EXTRA) + list(INJECT) + ["all"])
    ap.add_argument("--plan", action="store_true", help="print what a models.yaml entry will run, and stop")
    ap.add_argument("--variant", default="both", choices=list(VARIANTS) + list(INJECT_VARIANTS) + list(FOLLOWUP_VARIANTS) + ["batch", "both", "inject", "followup"])
    ap.add_argument("--limit", type=int, default=None, help="only this many uncached queries (smoke test)")
    ap.add_argument("--workers", type=int, default=None, help="queries in flight (default: the models.yaml concurrency, else 6)")
    ap.add_argument("--cache-as", default=None, help="write rows under this model key (a different backend via JEV_URL)")
    ap.add_argument("--shard", default="0/1", help="k/n: this process takes every n-th query starting at k")
    ap.add_argument("--reverse", action="store_true", help="walk datasets, variants and queries in reverse order")
    ap.add_argument("--slice", default="0/1", help="i/m: this process takes the i-th of m contiguous chunks of its shard")
    ap.add_argument("--skip-file", default=None, help="file of dataset|variant|qid lines to leave out (done elsewhere)")
    a = ap.parse_args()
    if a.plan:
        entry = MODELS.get(a.model) or KEY_ENTRY.get(a.model)
        print("\n".join(describe(entry)) if entry else f"{a.model} is a built-in model, not a models.yaml entry")
        raise SystemExit(0)
    if not a.dataset:
        ap.error("--dataset is required (or --plan)")
    if a.model in MODELS:
        print("\n".join(describe(MODELS[a.model])), flush=True)
    keys = MODELS[a.model].keys if a.model in MODELS else [a.model]
    if a.cache_as and len(keys) > 1:
        raise SystemExit(f"--cache-as names one folder, and {a.model} runs {len(keys)} modes; run them one key at a time")
    order = lambda xs: list(xs)[::-1] if a.reverse else list(xs)
    for key in keys:
        workers = a.workers or (KEY_ENTRY[key].concurrency if key in KEY_ENTRY else 6)
        for ds in order(DATASETS if a.dataset == "all" else [a.dataset]):
            for v in order(VARIANTS if a.variant == "both" else INJECT_VARIANTS if a.variant == "inject"
                            else FOLLOWUP_VARIANTS if a.variant == "followup" else [a.variant]):
                run(key, ds, v, a.limit, workers, a.cache_as, a.shard, a.reverse, a.slice, a.skip_file)
