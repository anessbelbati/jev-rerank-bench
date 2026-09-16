"""Is a gap real or luck? Paired bootstrap over the questions, from the cached answers. No API calls.

For every English dataset the per-question nDCG@10 and top-1 of every model are recomputed from cache/. The questions
are then resampled with replacement B times (the same resample applied to every model, so the comparison stays paired);
the 8-dataset average is rebuilt from each resample. For a pair of models the report is the observed gap, the 95%
percentile range of the gap across resamples, and a two-sided bootstrap p-value (twice the share of resamples where the
gap crosses zero). A range that excludes zero (p < 0.05) is called "real" in the post; anything else "within noise".
Writes results/significance.json.
"""
from __future__ import annotations

import json
import sys

import numpy as np

from common import BRIGHT, CANDIDATES, CACHE, DATASETS, ENGLISH, RESULTS, read_jsonl, jsonl_exists
from eval import MODELS, ndcg, order

B = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
SEED = 0
JEV = [m for m in MODELS if m.startswith("jev-") and m != "jev-choice-reversed"]   # the reversed run is a diagnostic, not a setup
OTHER = [m for m in MODELS if not m.startswith("jev-") and m != "bm25"]


def per_query(ds: str) -> tuple[list[str], dict[str, dict[str, np.ndarray]]]:
    cands = {r["qid"]: r for r in read_jsonl(CANDIDATES / f"{ds}.jsonl") if r["n_rel_top30"] > 0}
    runs = {}
    for m in MODELS:
        p = CACHE / m / f"{ds}.present.jsonl"
        if not jsonl_exists(p):
            continue
        rows = {r["qid"]: r for r in read_jsonl(p)}
        if all(q in rows and rows[q]["ok"] for q in cands):
            runs[m] = rows
    qids = sorted(cands)
    out = {"ndcg10": {}, "top1": {}}
    for m, rows in runs.items():
        ranked = [order(rows[q]) for q in qids]
        out["ndcg10"][m] = np.array([ndcg(r, cands[q]["relevant"]) for r, q in zip(ranked, qids)])
        out["top1"][m] = np.array([1.0 if r[0] in cands[q]["relevant"] else 0.0 for r, q in zip(ranked, qids)])
    return qids, out


def pair(boot: dict[str, np.ndarray], obs: dict[str, float], a: str, b: str) -> dict:
    d = boot[a] - boot[b]
    lo, hi = np.percentile(d, [2.5, 97.5])
    p = min(1.0, 2 * min(float((d <= 0).mean()), float((d >= 0).mean())))
    return {"a": a, "b": b, "diff": obs[a] - obs[b], "ci95": [float(lo), float(hi)], "p": p, "real": bool(p < 0.05)}


def main() -> dict:
    rng = np.random.default_rng(SEED)
    per_ds: dict[str, dict] = {}
    boot_ds: dict[str, dict[str, dict[str, np.ndarray]]] = {}
    obs_ds: dict[str, dict[str, dict[str, float]]] = {}
    for ds in [d for d in DATASETS if (CANDIDATES / f"{d}.jsonl").exists()]:
        qids, scores = per_query(ds)
        if not scores["ndcg10"]:
            continue
        n = len(qids)
        idx = rng.integers(0, n, size=(B, n))
        boot_ds[ds] = {met: {m: arr[idx].mean(axis=1) for m, arr in scores[met].items()} for met in scores}
        obs_ds[ds] = {met: {m: float(arr.mean()) for m, arr in scores[met].items()} for met in scores}
        o, bt = obs_ds[ds]["ndcg10"], boot_ds[ds]["ndcg10"]
        ranked = sorted(o, key=lambda m: -o[m])
        best_jev = max((m for m in JEV if m in o), key=lambda m: o[m]); best_other = max((m for m in OTHER if m in o), key=lambda m: o[m])
        per_ds[ds] = {"n": n, "first": pair(bt, o, ranked[0], ranked[1]), "jev_vs_other": pair(bt, o, best_jev, best_other),
                      "headline_pair": pair(bt, o, "jev-score-batch", "cohere-pro") if "jev-score-batch" in bt and "cohere-pro" in bt else None,
                      "top1_best_vs_runner_up": (lambda oo, bb: pair(bb, oo, *sorted(oo, key=lambda m: -oo[m])[:2]))(obs_ds[ds]["top1"], boot_ds[ds]["top1"])}
        f = per_ds[ds]["jev_vs_other"]
        print(f"{ds:17} n={n:3}  best Jev {best_jev} vs best other {best_other}: gap {f['diff']:+.3f} "
              f"[{f['ci95'][0]:+.3f}, {f['ci95'][1]:+.3f}] p={f['p']:.3f} {'REAL' if f['real'] else 'within noise'}")

    overall = {}
    pairs = {}
    for met in ("ndcg10", "top1"):
        models = [m for m in MODELS if not m.endswith("-reversed") and all(m in boot_ds[ds][met] for ds in ENGLISH)]
        boot = {m: np.mean([boot_ds[ds][met][m] for ds in ENGLISH], axis=0) for m in models}
        obs = {m: float(np.mean([obs_ds[ds][met][m] for ds in ENGLISH])) for m in models}
        best = max(models, key=lambda m: obs[m])
        overall[met] = {"best": best, "mean": obs, "vs_best": {m: pair(boot, obs, best, m) for m in models if m != best}}
        pairs[met] = {f"{a}|{b}": pair(boot, obs, a, b) for a, b in (("jev-score-batch", "cohere-pro"), ("jev-choice", "cohere-pro"),
                                                                       ("jev-noul-batch", "cohere-pro"), ("jev-score-batch", "zerank-2"),
                                                                       ("jev-choice", "jev-score-batch"), ("cohere-pro", "zerank-2"),
                                                                       ("jev-score-batch", "deepseek-json"), ("jev-score-batch", "jev-noul-pair"),
                                                                       ("qwen-rlcd-pair", "bm25"), ("qwen-rlcd-batch", "bm25"), ("qwen-rlcd-pair", "qwen-rlcd-batch"))
                      if a in boot and b in boot}
        print(f"\n8-dataset average, {met}: best = {best} ({obs[best]:.3f})")
        for m in sorted(models, key=lambda m: -obs[m]):
            if m == best:
                continue
            v = overall[met]["vs_best"][m]
            print(f"   vs {m:20} {obs[m]:.3f}  gap {v['diff']:+.3f} [{v['ci95'][0]:+.3f}, {v['ci95'][1]:+.3f}] p={v['p']:.3f} {'REAL' if v['real'] else 'within noise'}")
    bright = {}
    bsets = [d for d in BRIGHT if d in boot_ds]
    for met in ("ndcg10", "top1"):
        models = [m for m in MODELS if not m.endswith("-reversed") and all(m in boot_ds[ds][met] for ds in bsets)]
        boot = {m: np.mean([boot_ds[ds][met][m] for ds in bsets], axis=0) for m in models}
        obs = {m: float(np.mean([obs_ds[ds][met][m] for ds in bsets])) for m in models}
        best = max(models, key=lambda m: obs[m])
        best_jev = max((m for m in JEV if m in obs), key=lambda m: obs[m]); best_other = max((m for m in OTHER if m in obs), key=lambda m: obs[m])
        bright[met] = {"datasets": bsets, "n": sum(per_ds[d]["n"] for d in bsets), "best": best, "mean": obs,
                       "vs_best": {m: pair(boot, obs, best, m) for m in models if m != best},
                       "jev_vs_other": pair(boot, obs, best_jev, best_other)}
        j = bright[met]["jev_vs_other"]
        print(f"\nBRIGHT block ({len(bsets)} subsets, {bright[met]['n']} questions), {met}: best Jev {best_jev} vs best other {best_other}: "
              f"gap {j['diff']:+.3f} [{j['ci95'][0]:+.3f}, {j['ci95'][1]:+.3f}] p={j['p']:.3f} {'REAL' if j['real'] else 'within noise'}")
    return {"B": B, "seed": SEED, "datasets": per_ds, "overall": overall, "pairs": pairs, "bright": bright}


if __name__ == "__main__":
    res = main()
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "significance.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("wrote", RESULTS / "significance.json")
