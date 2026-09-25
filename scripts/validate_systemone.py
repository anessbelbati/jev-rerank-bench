"""Check rerankers/systemone.py against Jev: every saved Jev answer replayed through it, then real Jev called live.

    uv run scripts/validate_systemone.py              # replay only: no API calls, no cost
    uv run scripts/validate_systemone.py --live 25    # plus 25 live queries per mode, through systemone.py and jev.py
    uv run scripts/validate_systemone.py --live 25 --route openrouter   # the same, through OpenRouter's typesafe/jev-1.13

Replay: every saved row of the eight Jev setups behind the headline (the eight English datasets, both variants, plus
NevIR) has its saved responses fed back, in call order, to jev.py and to systemone.py set up for Jev. Both must send
byte-identical requests (URL, headers, body), and systemone.py must give the saved scores, extras and cost exactly.

Live: Jev does not return identical answers twice (results/determinism.json: 1% of repeated batch calls identical, the
top pick changed on 3 of 100), so a live rerun cannot equal the cache. The same sampled queries go to real Jev through
systemone.py and through jev.py, back to back; each is compared with the cache and with the other. systemone.py
reproduces the cached results if its gap to the cache is the size of jev.py's own gap, measured the same minute.
Writes results/systemone_validation.txt and the live responses to results/systemone_validation.live.jsonl.gz.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import random
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import rerankers.jev as jev  # noqa: E402
import rerankers.systemone as so  # noqa: E402
from common import CACHE, CANDIDATES, ENGLISH, PRICES, RESULTS, read_jsonl, truncate  # noqa: E402

JEV = so.Endpoint("https://api.typesafe.ai/v1", "jev-latest", "JEV_API_KEY", PRICES["jev"]["input_per_m"], PRICES["jev"]["output_per_m"])
# Live calls can also go through OpenRouter's System One route (same Jev, billed by OpenRouter); jev.py is pointed at
# the same route for its side of the comparison.
ROUTES = {"typesafe": JEV, "openrouter": so.Endpoint("https://openrouter.ai/api/v1", "typesafe/jev-1.13", "OPENROUTER_API_KEY")}
OLD = {"noul-pair": jev.JevNoulPair, "noul-batch": jev.JevNoulBatch, "choice": jev.JevChoice,
       "choice-reversed": jev.JevChoiceReversed, "score-batch": jev.JevScoreBatch, "duel": jev.JevDuel,
       "tournament": jev.JevTournament, "cascade": jev.JevCascade}
SETS = [(ds, v) for ds in ENGLISH for v in ("present", "absent")] + [("nevir", "present")]
REAL_POST = so.post_json
REPORT, LIVE_ROWS = RESULTS / "systemone_validation.txt", RESULTS / "systemone_validation.live.jsonl.gz"


class Replay:
    """Stands in for common.post_json: answers each request with the next saved response and keeps the request."""

    def __init__(self, calls: list[dict]):
        self.calls, self.sent = calls, []

    def __call__(self, url, headers, body, **_):
        c = self.calls[len(self.sent)]
        self.sent.append((url, json.dumps(headers, sort_keys=True), json.dumps(body)))
        return c["status"], c["raw"], c["latency_ms"], {}


def load(ds: str) -> tuple[dict, dict]:
    cands = {r["qid"]: r for r in read_jsonl(CANDIDATES / f"{ds}.jsonl")}
    docs = {r["did"]: r["text"] for r in read_jsonl(CANDIDATES / f"{ds}.docs.jsonl")}
    return cands, docs


def inputs(cand: dict, variant: str, docs: dict) -> tuple[list[str], list[str]]:
    """Exactly what run.py hands a reranker: the variant's candidates, each cut to MAX_CHARS."""
    cs = cand[variant]
    return [c["did"] for c in cs], [truncate(docs[c["did"]]) for c in cs]


def canon(x) -> str:
    return json.dumps(x, sort_keys=True)


def extra_match(new: dict, saved: dict) -> str:
    """'same'; 'older' when the saved row predates the reversed flag (the first Sept 16 Choice rows) and every other
    field is equal; else 'diff'."""
    if canon(new) == canon(saved):
        return "same"
    if "reversed" not in saved and new.get("reversed") is False and canon({k: v for k, v in new.items() if k != "reversed"}) == canon(saved):
        return "older"
    return "diff"


def replay_all() -> tuple[list[str], bool]:
    lines, all_ok = [], True
    assert (jev.URL, jev.MODEL) == (JEV.url, JEV.model), "unset JEV_URL / JEV_MODEL: the check is against Jev itself"
    stats = {m: dict(rows=0, skipped_failed=0, same_requests=0, calls=0, scores=0, extras=0, older=0, cost=0, old_scores=0,
                     old_extras=0) for m in OLD}
    first_bad: dict[str, str] = {}
    for ds, variant in SETS:
        cands, docs = load(ds)
        for mode in OLD:
            for row in read_jsonl(CACHE / f"jev-{mode}" / f"{ds}.{variant}.jsonl"):
                s = stats[mode]
                if not row["ok"]:
                    s["skipped_failed"] += 1
                    continue
                s["rows"] += 1
                dids, texts = inputs(cands[row["qid"]], variant, docs)
                assert dids == row["dids"], (mode, ds, variant, row["qid"])
                sent, res = {}, {}
                for side, mod, build in (("old", jev, OLD[mode]), ("new", so, lambda m=mode: so.make(JEV, m))):
                    r = Replay(row["calls"])
                    mod.post_json = r
                    try:
                        res[side] = build().rerank(row_query(cands, row), texts)
                    except IndexError:          # asked more requests than were saved
                        res[side] = None
                    sent[side] = r.sent
                new, old = res["new"], res["old"]
                good_req = sent["old"] == sent["new"] and new is not None
                em = extra_match(new.extra, row["extra"]) if new is not None else "diff"
                good = (good_req and len(sent["new"]) == len(row["calls"]) and new.scores == row["scores"] and em != "diff"
                        and new.cost_usd == row["cost_usd"])
                s["same_requests"] += good_req
                s["calls"] += len(sent["new"]) == len(row["calls"])
                s["scores"] += new is not None and new.scores == row["scores"]
                s["extras"] += em != "diff"
                s["older"] += em == "older"
                s["cost"] += new is not None and new.cost_usd == row["cost_usd"]
                s["old_scores"] += old is not None and old.scores == row["scores"]
                s["old_extras"] += old is not None and new is not None and canon(old.extra) == canon(new.extra)
                if mode not in first_bad and not good:
                    first_bad[mode] = f"{ds}.{variant} qid {row['qid']}"
    so.post_json = jev.post_json = REAL_POST
    lines.append("REPLAY: saved Jev responses fed back through jev.py and systemone.py (no API calls)")
    lines.append(f"{'mode':16} {'rows':>6} {'same requests':>14} {'all responses used':>19} {'same scores':>12} {'same extras':>12} {'same cost':>10}")
    for mode, s in stats.items():
        n = s["rows"]
        lines.append(f"{mode:16} {n:6} {s['same_requests']:14} {s['calls']:19} {s['scores']:12} {s['extras']:12} {s['cost']:10}"
                     + (f"   (+{s['skipped_failed']} failed rows skipped)" if s["skipped_failed"] else ""))
        if not (s["same_requests"] == s["calls"] == s["scores"] == s["extras"] == s["cost"] == s["old_extras"] == n):
            all_ok = False
        if s["older"]:
            lines.append(f"  {s['older']} saved {mode} rows predate the 'reversed' flag in the extras (first Sept 16 runs); "
                         f"every other field equal")
        if s["old_scores"] != n:
            lines.append(f"  note: jev.py itself gives the saved scores on {s['old_scores']} of {n} rows")
        if s["old_extras"] != n:
            lines.append(f"  jev.py and systemone.py extras equal on {s['old_extras']} of {n} rows")
    for mode, where in first_bad.items():
        lines.append(f"  first difference, {mode}: {where}")
    lines.append("replay: EXACT on every row" if all_ok else "replay: DIFFERENCES above")
    return lines, all_ok


def row_query(cands: dict, row: dict) -> str:
    return cands[row["qid"]]["query"]


def ranked(dids: list[str], scores: list[float]) -> list[str]:
    return [dids[i] for i in sorted(range(len(dids)), key=lambda i: -scores[i])]


def ndcg10(order: list[str], rel: dict) -> float:
    dcg = lambda gains: sum(g / math.log2(i + 2) for i, g in enumerate(gains))
    ideal = dcg(sorted(rel.values(), reverse=True)[:10])
    return dcg([rel.get(d, 0) for d in order[:10]]) / ideal if ideal else 0.0


def live(n: int, workers: int, route: str) -> list[str]:
    ep = ROUTES[route]
    jev.URL, jev.MODEL, jev.VIA_OPENROUTER = ep.url, ep.model, "openrouter.ai" in ep.url
    data = {ds: load(ds) for ds in ENGLISH}
    saved = {m: {ds: {r["qid"]: r for r in read_jsonl(CACHE / f"jev-{m}" / f"{ds}.present.jsonl") if r["ok"]} for ds in ENGLISH} for m in OLD}
    pool = [(ds, q) for ds in ENGLISH for q, c in sorted(data[ds][0].items())
            if c["n_rel_top30"] > 0 and all(q in saved[m][ds] for m in OLD)]
    sample = random.Random(20260924).sample(pool, n)

    def one(task):
        mode, i, (ds, q) = task
        cands, docs = data[ds]
        dids, texts = inputs(cands[q], "present", docs)
        out = {}
        for side in (("systemone", "jev.py") if i % 2 == 0 else ("jev.py", "systemone")):     # alternate who goes first
            t0 = time.perf_counter()
            res = (so.make(ep, mode) if side == "systemone" else OLD[mode]()).rerank(cands[q]["query"], texts)
            out[side] = {"side": side, "mode": mode, "dataset": ds, "qid": q, "variant": "present", "dids": dids,
                         "scores": res.scores, "extra": res.extra, "ok": res.ok, "cost_usd": res.cost_usd,
                         "query_ms": (time.perf_counter() - t0) * 1000, "calls": [asdict(c) for c in res.calls],
                         "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        return out

    tasks = [(m, i, dq) for m in OLD for i, dq in enumerate(sample)]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(one, tasks))
    with gzip.open(LIVE_ROWS, "wt", encoding="utf-8") as f:
        for pair in results:
            for row in pair.values():
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    versions = sorted({c["raw"].get("model") for pair in results for row in pair.values() for c in row["calls"] if isinstance(c.get("raw"), dict)} - {None})
    cost = sum(row["cost_usd"] for pair in results for row in pair.values())
    failed = sum(not row["ok"] for pair in results for row in pair.values())
    lines = [f"LIVE: {n} queries per mode (seed 20260924, present variant, questions with a labelled answer in the 30), "
             f"sent to {ep.url} model {ep.model} through both files, back to back",
             f"reported model now: {', '.join(versions)}; cached rows: jev-1.13.0.  live cost ${cost:.3f}; failed queries {failed}",
             "top = same top-ranked passage; gap = mean over queries of the largest score difference on any passage;",
             "nDCG@10 on the sample for the cached run, systemone.py live and jev.py live",
             f"{'mode':16} {'systemone vs cache':>21} {'jev.py vs cache':>18} {'systemone vs jev.py':>21} {'nDCG cache / sys1 / jev.py':>28}"]
    for mode in OLD:
        rows = [p for p in results if p["systemone"]["mode"] == mode and p["systemone"]["ok"] and p["jev.py"]["ok"]]

        def cmp(a_of, b_of):
            top = sum(ranked(a_of(p)["dids"], a_of(p)["scores"])[0] == ranked(b_of(p)["dids"], b_of(p)["scores"])[0] for p in rows)
            gap = statistics.mean(max(abs(x - y) for x, y in zip(a_of(p)["scores"], b_of(p)["scores"])) for p in rows)
            return f"{top}/{len(rows)} top, gap {gap:.3f}"

        cache_of = lambda p: saved[mode][p["systemone"]["dataset"]][p["systemone"]["qid"]]
        nd = lambda of: statistics.mean(ndcg10(ranked(of(p)["dids"], of(p)["scores"]),
                                               data[p["systemone"]["dataset"]][0][p["systemone"]["qid"]]["relevant"]) for p in rows)
        lines.append(f"{mode:16} {cmp(lambda p: p['systemone'], cache_of):>21} {cmp(lambda p: p['jev.py'], cache_of):>18} "
                     f"{cmp(lambda p: p['systemone'], lambda p: p['jev.py']):>21} "
                     f"{nd(cache_of):.3f} / {nd(lambda p: p['systemone']):.3f} / {nd(lambda p: p['jev.py']):.3f}".rjust(28))
    return lines


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", type=int, default=0, help="also call real Jev on this many sampled queries per mode")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--route", choices=sorted(ROUTES), default="typesafe", help="where the live calls go")
    a = ap.parse_args()
    out, exact = replay_all()
    print("\n".join(out), flush=True)
    if a.live and exact:
        out += [""] + live(a.live, a.workers, a.route)
        print("\n".join(out[-(len(OLD) + 5):]))
    elif a.live:
        print("live check skipped: the replay must be exact first")
    REPORT.write_text("\n".join(out) + "\n", encoding="utf-8")
    sys.exit(0 if exact else 1)
