"""Test your own model: run a models.yaml entry through the benchmark and print its rows for the README's main table.

    uv run bench.py <name> --smoke     # 20 SciFact questions per mode: does the server answer, and what would the full run take
    uv run bench.py <name>             # every mode on the 8 headline datasets (both lists) and NevIR, then the rows
    uv run bench.py <name> --score     # only print the rows, from the responses already in cache/

Responses go to cache/<name>-<mode>/ in run.py's format; a rerun skips every question already answered and retries
the failed ones. At the end they are packed like the rest of cache/ (one row per question, gzipped). The rows are
scored with eval.py's own functions, the way the README's main table is: nDCG@10 with each dataset counting once and
with each question counting once, NevIR pairs right (nevir_eval.py's rule: a tie is wrong), top pick right, time per
query (mean of the dataset medians), $ per 1,000 queries (mean of the dataset rates) and the "nothing here" AUROC.
"""
from __future__ import annotations

import argparse
import gzip
import json
import statistics
import sys

from common import CACHE, CANDIDATES, DATASETS, ENGLISH, read_jsonl
from eval import auroc, load_run, ndcg, order
from rerankers import MODELS
from rerankers.registry import Entry, describe
from run import run

MODE_WORDS = {"noul-pair": "yes/no per pair", "score-pair": "4-level rubric per pair", "noul-batch": "30 yes/no in one call",
              "choice": "one Choice + none", "choice-reversed": "one Choice, passages reversed",
              "score-batch": "4-level rubric, 30 in one call", "duel": "45 duels in one call (top 10)",
              "tournament": "tournament (6 groups, then final)", "cascade": "cascade (batch prune, then 8 pairs)"}
SMOKE_SET = ("scifact", "present")


def sets(all_datasets: bool) -> list[tuple[str, str]]:
    return [(ds, v) for ds in (DATASETS if all_datasets else ENGLISH) for v in ("present", "absent")] + [("nevir", "present")]


def wanted(ds: str, variant: str) -> list[str]:
    return [r["qid"] for r in read_jsonl(CANDIDATES / f"{ds}.jsonl") if r[variant]]


def pack(key: str, ds: str, variant: str) -> tuple[int, int, int, int]:
    """One row per question into <ds>.<variant>.jsonl.gz, in list order; a failed row never replaces an ok one.
    Returns (wanted, ok, failed, missing)."""
    plain = CACHE / key / f"{ds}.{variant}.jsonl"
    got: dict[str, dict] = {}
    for r in read_jsonl(plain):
        cur = got.get(r["qid"])
        if cur is None or r["ok"] or not cur["ok"]:
            got[r["qid"]] = r
    want = wanted(ds, variant)
    if plain.exists():
        with gzip.open(plain.with_name(plain.name + ".gz"), "wt", encoding="utf-8") as f:
            for q in want:
                if q in got:
                    f.write(json.dumps(got[q], ensure_ascii=False) + "\n")
        plain.unlink()
    ok = sum(1 for q in want if q in got and got[q]["ok"])
    failed = sum(1 for q in want if q in got and not got[q]["ok"])
    return len(want), ok, failed, len(want) - ok - failed


def score(key: str) -> dict:
    """The main table's numbers for one model key, from cache/."""
    per, pooled, missing = [], [], []
    for ds in ENGLISH:
        cands = {r["qid"]: r for r in read_jsonl(CANDIDATES / f"{ds}.jsonl")}
        present, absent = load_run(key, ds, "present"), load_run(key, ds, "absent")
        ok = [q for q, c in cands.items() if c["n_rel_top30"] > 0 and q in present and present[q]["ok"]]
        if not ok:
            missing.append(ds)
            continue
        nd = [ndcg(order(present[q]), cands[q]["relevant"]) for q in ok]
        pooled += nd
        rows = [r for r in list(present.values()) + list(absent.values()) if r["ok"]]
        both = [q for q in ok if q in absent and absent[q]["ok"]]
        per.append({"ndcg": statistics.mean(nd),
                    "top1": statistics.mean(1.0 if order(present[q])[0] in cands[q]["relevant"] else 0.0 for q in ok),
                    "ms": statistics.median(r["query_ms"] for r in rows),
                    "cost": sum(r["cost_usd"] for r in present.values()) / len(present) * 1000,
                    "auroc": auroc([max(present[q]["scores"]) for q in both], [max(absent[q]["scores"]) for q in both]) if both else None})
    out = {"missing": missing, "questions": len(pooled), "nevir": nevir(key)}
    if per:
        mean = lambda k: statistics.mean(p[k] for p in per if p[k] is not None) if any(p[k] is not None for p in per) else None
        out.update({"ndcg_datasets": mean("ndcg"), "ndcg_questions": statistics.mean(pooled), "top1": mean("top1"),
                    "ms": mean("ms"), "cost": mean("cost"), "auroc": mean("auroc")})
    return out


def nevir(key: str) -> float | None:
    """Paired accuracy: a pair is right only if each question scores its own passage strictly above the other."""
    rows = load_run(key, "nevir", "present")
    if not rows:
        return None
    pairs: dict[str, dict] = {}
    for c in read_jsonl(CANDIDATES / "nevir.jsonl"):
        pairs.setdefault(c["pair"], {})[c["qid"][-2:]] = c
    results = []
    for qs in pairs.values():
        rs = [rows.get(qs[k]["qid"]) for k in ("q1", "q2")]
        if not all(r and r["ok"] for r in rs):
            return None                      # an incomplete NevIR run gets no number
        right = []
        for k, r in zip(("q1", "q2"), rs):
            s = dict(zip(r["dids"], r["scores"]))
            rel = next(iter(qs[k]["relevant"]))
            right.append(all(s[rel] > v for d, v in s.items() if d != rel))
        results.append(all(right))
    return statistics.mean(results)


def fmt_row(name: str, runs_on: str, m: dict) -> str:
    pct = lambda x: "—" if x is None else f"{x:.0%}"
    time = f"{m['ms'] / 1000:.1f} s" if m["ms"] >= 1000 else f"{m['ms']:.0f} ms"
    cells = [name, runs_on, f"{m['ndcg_datasets']:.3f}", f"{m['ndcg_questions']:.3f}", pct(m["nevir"]), pct(m["top1"]), time,
             f"{m['cost']:.2f}", "—" if m["auroc"] is None else f"{m['auroc']:.2f}"]
    return "| " + " | ".join(cells) + " |"


def runs_on(entry: Entry) -> str:
    if entry.runs_on:
        return entry.runs_on
    return "Self-hosted" if entry.endpoint.gpu_usd_per_hour is not None else "API"


def print_rows(entry: Entry) -> bool:
    short = (entry.label or entry.name).split(" (")[0]
    complete = True
    print("\nRows for the README's main table (API rows go with the API group, self-hosted with the self-hosted group, by score):")
    for step_key in entry.keys:
        mode = next(s.mode for s in entry.steps if s.key == step_key)
        m = score(step_key)
        if m["missing"] or m["nevir"] is None:
            complete = False
            print(f"  {step_key}: not complete yet (no scored questions on {', '.join(m['missing']) or 'none'}; "
                  f"NevIR {'complete' if m['nevir'] is not None else 'incomplete'})")
        if "ndcg_datasets" in m:
            print(fmt_row(f"{short} {MODE_WORDS[mode]}", runs_on(entry), m) + ("" if not m["missing"] else "   <- partial, not for the README"))
    return complete


def smoke(entry: Entry, n: int, workers: int, all_datasets: bool) -> None:
    ds, variant = SMOKE_SET
    total = sum(len(wanted(d, v)) for d, v in sets(all_datasets))
    first = wanted(ds, variant)[:n]
    for key in entry.keys:
        saved = load_run(key, ds, variant)
        todo = sum(1 for q in first if not (q in saved and saved[q]["ok"]))
        if todo:        # run.py takes unanswered questions in list order, so these are exactly the first n still open
            run(key, ds, variant, todo, workers)
            saved = load_run(key, ds, variant)
        rows = [saved[q] for q in first if q in saved]
        ok = [r for r in rows if r["ok"]]
        print(f"\n{key}: {len(ok)} of {len(rows)} smoke questions answered")
        for r in rows:
            if not r["ok"]:
                err = next((c for c in r["calls"] if c.get("error")), {})
                print(f"  first failure, question {r['qid']}: {err.get('error')} {str(err.get('raw'))[:300]}")
                break
        if ok:
            med_ms = statistics.median(r["query_ms"] for r in ok)
            per_q = statistics.mean(r["cost_usd"] for r in ok)
            hours = total * med_ms / workers / 3.6e6
            print(f"  median {med_ms / 1000:.1f} s per question, ${per_q * 1000:.2f} per 1,000 questions; the full run is "
                  f"{total:,} questions: about {hours:.1f} h at {workers} at a time, about ${per_q * total:.2f} of calls")


def full(entry: Entry, workers: int, all_datasets: bool) -> None:
    for key in entry.keys:
        for ds, variant in sets(all_datasets):
            run(key, ds, variant, None, workers)
    print("\nPacked into cache/ (wanted / ok / failed / missing):")
    for key in entry.keys:
        for ds, variant in sets(all_datasets):
            w, ok, failed, missing = pack(key, ds, variant)
            print(f"  {key:32} {ds:26} {variant:8} {w:5} {ok:5} {failed:4} {missing:4}" + ("" if ok == w else "   <- rerun to retry"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("name", choices=sorted(MODELS), help="a models.yaml entry")
    ap.add_argument("--smoke", nargs="?", type=int, const=20, default=None, help="only N SciFact questions per mode (default 20)")
    ap.add_argument("--score", action="store_true", help="only print the rows, from cache/")
    ap.add_argument("--all-datasets", action="store_true", help="also the five later BRIGHT subsets and MIRACL French")
    ap.add_argument("--workers", type=int, default=None, help="questions in flight (default: the entry's concurrency)")
    a = ap.parse_args()
    entry = MODELS[a.name]
    workers = a.workers or entry.concurrency
    print("\n".join(describe(entry)), flush=True)
    if a.smoke is not None:
        smoke(entry, a.smoke, workers, a.all_datasets)
        return
    if not a.score:
        full(entry, workers, a.all_datasets)
    sys.exit(0 if print_rows(entry) else 1)


if __name__ == "__main__":
    main()
