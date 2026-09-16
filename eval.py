"""Score every cached run: ranking quality, latency, cost, the "nothing relevant" test and calibration.

    uv run eval.py            # writes results/summary.md, results/summary.json and the charts

Ranking metrics are computed only over queries whose BM25 top-30 holds at least one relevant passage: a reranker can
reorder the 30, it cannot conjure a passage BM25 never returned. The count of such queries is printed with every table.
"""
from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from common import CACHE, CANDIDATES, DATASETS, ENGLISH, RESULTS, read_jsonl, jsonl_exists  # noqa: E402

MODELS = ["bm25", "cohere-pro", "cohere-fast", "zerank-2", "deepseek-pair", "deepseek-json",
          "jev-noul-pair", "jev-noul-batch", "jev-choice",
          "jev-score-batch", "jev-duel", "jev-tournament", "jev-cascade", "jev-choice-reversed",
          "qwen-rlcd-batch", "qwen-rlcd-rubric", "qwen-rlcd-pair", "qwen-rlcd-batch-reversed"]
LABELS = {"bm25": "BM25 (floor)", "cohere-pro": "Cohere Rerank 4 Pro", "cohere-fast": "Cohere Rerank 4 Fast",
          "zerank-2": "ZeroEntropy zerank-2",
          "deepseek-pair": "DeepSeek V4.1 Flash P(yes) per pair", "deepseek-json": "DeepSeek V4.1 Flash JSON, 30 in one call",
          "jev-noul-pair": "Jev yes/no per pair", "jev-noul-batch": "Jev 30 yes/no in one call", "jev-choice": "Jev one Choice + none",
          "jev-score-batch": "Jev 4-level rubric, 30 in one call", "jev-duel": "Jev 45 duels in one call (top 10)",
          "jev-tournament": "Jev tournament (6 groups, then final)", "jev-cascade": "Jev cascade (batch prune, then 8 pairs)",
          "jev-choice-reversed": "Jev one Choice, passages reversed",
          "qwen-rlcd-batch": "Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted)", "qwen-rlcd-rubric": "Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted)",
          "qwen-rlcd-pair": "Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted)", "qwen-rlcd-batch-reversed": "Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed"}
# Models whose scores are presented as probabilities and so can be held to calibration.
PROB_MODELS = {"jev-noul-pair", "jev-noul-batch", "deepseek-pair", "qwen-rlcd-batch", "qwen-rlcd-pair"}


def load_run(model: str, dataset: str, variant: str) -> dict[str, dict]:
    p = CACHE / model / f"{dataset}.{variant}.jsonl"
    return {r["qid"]: r for r in read_jsonl(p)} if jsonl_exists(p) else {}


def order(row: dict) -> list[str]:
    """Candidate ids best first: score descending, ties keep BM25 order."""
    idx = sorted(range(len(row["dids"])), key=lambda i: -row["scores"][i])
    return [row["dids"][i] for i in idx]


def order_worst(row: dict) -> list[str]:
    """Same, but ties broken against the model (reverse BM25 order): the pessimistic reading of a saturated scorer."""
    idx = sorted(range(len(row["dids"])), key=lambda i: (-row["scores"][i], -i))
    return [row["dids"][i] for i in idx]


def ndcg(ranked: list[str], rel: dict[str, int], k: int = 10) -> float:
    dcg = sum(rel.get(d, 0) / math.log2(i + 2) for i, d in enumerate(ranked[:k]))
    ideal = sorted(rel.values(), reverse=True)[:k]
    idcg = sum(g / math.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg if idcg else 0.0


def recall(ranked: list[str], rel: dict[str, int], k: int = 5) -> float:
    return len(set(ranked[:k]) & set(rel)) / len(rel)


def mrr(ranked: list[str], rel: dict[str, int], k: int = 10) -> float:
    for i, d in enumerate(ranked[:k]):
        if d in rel:
            return 1 / (i + 1)
    return 0.0


def auroc(pos: list[float], neg: list[float]) -> float:
    """Chance that a random query-with-an-answer scores above a random query-without. 0.5 = coin flip."""
    if not pos or not neg:
        return float("nan")
    wins = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def percentile(xs: list[float], q: float) -> float:
    s = sorted(xs)
    return s[min(len(s) - 1, int(round(q * (len(s) - 1))))]


def calibration(pairs: list[tuple[float, int]], bins: int = 10):
    """pairs = (score, relevant 0/1). Returns per-bin rows and the expected calibration error."""
    rows, ece, n = [], 0.0, len(pairs)
    for b in range(bins):
        lo, hi = b / bins, (b + 1) / bins
        inb = [(s, r) for s, r in pairs if (lo <= s < hi) or (b == bins - 1 and s == 1.0)]
        if not inb:
            rows.append({"bin": f"{lo:.1f}-{hi:.1f}", "n": 0, "mean_score": None, "frac_relevant": None})
            continue
        ms = sum(s for s, _ in inb) / len(inb)
        fr = sum(r for _, r in inb) / len(inb)
        ece += len(inb) / n * abs(fr - ms)
        rows.append({"bin": f"{lo:.1f}-{hi:.1f}", "n": len(inb), "mean_score": round(ms, 3), "frac_relevant": round(fr, 3)})
    return rows, ece


def evaluate() -> dict:
    out: dict = {"datasets": {}, "models": MODELS}
    for ds in DATASETS:
        if not (CANDIDATES / f"{ds}.jsonl").exists():
            continue
        cands = {r["qid"]: r for r in read_jsonl(CANDIDATES / f"{ds}.jsonl")}
        eval_qids = [q for q, r in cands.items() if r["n_rel_top30"] > 0]
        dsres = {"queries_total": len(cands), "queries_with_answer_in_top30": len(eval_qids), "models": {}}
        for m in MODELS:
            present, absent = load_run(m, ds, "present"), load_run(m, ds, "absent")
            if not present:
                continue
            ok = [q for q in eval_qids if q in present and present[q]["ok"]]
            if not ok:
                continue
            nd = [ndcg(order(present[q]), cands[q]["relevant"]) for q in ok]
            nd_w = [ndcg(order_worst(present[q]), cands[q]["relevant"]) for q in ok]
            tied = sum(1 for q in ok if present[q]["scores"].count(max(present[q]["scores"])) > 1)
            zeros = sum(1 for q in ok for x in present[q]["scores"] if x <= 1e-6)
            saturated = sum(1 for q in ok for x in present[q]["scores"] if x <= 1e-6 or x >= 1 - 1e-6)
            n_scores = sum(len(present[q]["scores"]) for q in ok)
            r5 = [recall(order(present[q]), cands[q]["relevant"]) for q in ok]
            t1 = [1.0 if order(present[q])[0] in cands[q]["relevant"] else 0.0 for q in ok]
            rr = [mrr(order(present[q]), cands[q]["relevant"]) for q in ok]
            allrows = list(present.values()) + list(absent.values())
            lat = [c["latency_ms"] for r in allrows for c in r["calls"] if c["status"] == 200]
            qlat = [r["query_ms"] for r in allrows if r["ok"]]
            cost_present = sum(present[q]["cost_usd"] for q in present)
            usage = defaultdict(float)
            for r in allrows:
                for c in r["calls"]:
                    for k, v in (c.get("usage") or {}).items():
                        if isinstance(v, (int, float)):
                            usage[k] += v
            res = {
                "n": len(ok), "failed": sum(1 for q in eval_qids if q in present and not present[q]["ok"]),
                "ndcg10": statistics.mean(nd), "recall5": statistics.mean(r5), "top1": statistics.mean(t1), "mrr10": statistics.mean(rr),
                "ndcg10_ties_against": statistics.mean(nd_w), "tied_top_share": tied / len(ok), "zero_score_share": zeros / n_scores, "saturated_share": saturated / n_scores,
                "calls": len(lat), "call_ms_median": statistics.median(lat) if lat else None,
                "call_ms_p95": percentile(lat, 0.95) if lat else None,
                "query_ms_median": statistics.median(qlat) if qlat else None,
                "cost_usd_present": cost_present, "cost_per_1k_queries": cost_present / len(present) * 1000 if present else None,
                "cost_usd_all_variants": sum(r["cost_usd"] for r in allrows), "usage_totals": dict(usage),
                "workers": present[ok[0]].get("workers"),
            }
            # Nothing-relevant test: same queries, answer present vs removed. Signal = the model's top score.
            both = [q for q in ok if q in absent and absent[q]["ok"]]
            if both:
                pos = [max(present[q]["scores"]) for q in both]
                neg = [max(absent[q]["scores"]) for q in both]
                thr = percentile(pos, 0.10)  # keep 90% of real answers...
                signals = {"max_score": (pos, neg)}
                if m == "jev-choice":
                    signals["1-P(none)"] = ([1 - present[q]["extra"]["none_prob"] for q in both], [1 - absent[q]["extra"]["none_prob"] for q in both])
                    signals["P(any)"] = ([present[q]["extra"]["any_prob"] for q in both], [absent[q]["extra"]["any_prob"] for q in both])
                none = {}
                for name, (p, n_) in signals.items():
                    t = percentile(p, 0.10)
                    none[name] = {"auroc": auroc(p, n_), "threshold_keeping_90pct_answers": t,
                                  "false_accept_rate": sum(1 for x in n_ if x >= t) / len(n_),
                                  "median_present": statistics.median(p), "median_absent": statistics.median(n_)}
                res["nothing_relevant"] = {"n_pairs": len(both), "signals": none}
            # Calibration over every (passage, score) in the present variant.
            pairs = [(s, 1 if d in cands[q]["relevant"] else 0) for q in ok for d, s in zip(present[q]["dids"], present[q]["scores"])]
            if all(0.0 <= s <= 1.0 for s, _ in pairs):
                rows, ece = calibration(pairs)
                res["calibration"] = {"ece": ece, "bins": rows, "is_probability_claim": m in PROB_MODELS,
                                      "n_pairs": len(pairs), "base_rate": sum(r for _, r in pairs) / len(pairs)}
            dsres["models"][m] = res
        dsres["thresholds"] = thresholds(ds, cands, eval_qids)
        dsres["position_bias"] = position_bias(ds, cands, eval_qids)
        dsres["position_bias_qwen"] = position_bias(ds, cands, eval_qids, "qwen-rlcd-batch", "qwen-rlcd-batch-reversed")
        out["datasets"][ds] = dsres
    return out


def thresholds(ds: str, cands: dict, eval_qids: list[str]) -> dict:
    """TypeSafe's documented bands (<0.5 route to a human, 0.5-0.9 proceed with care, >0.9 act) tested on real data:
    for Jev Choice, how often is the top pick right in each confidence band, and how often does it say none?"""
    out = {}
    for m in ("jev-choice", "jev-tournament"):
        present = load_run(m, ds, "present")
        if not present:
            continue
        bands = {"<0.5": [], "0.5-0.9": [], ">=0.9": []}
        for q in eval_qids:
            r = present.get(q)
            if not r or not r["ok"] or r["extra"].get("confidence") is None:
                continue
            c = r["extra"]["confidence"]
            band = "<0.5" if c < 0.5 else "0.5-0.9" if c < 0.9 else ">=0.9"
            picked_none = r["extra"].get("choice") == "none"
            top1_right = order(r)[0] in cands[q]["relevant"]
            bands[band].append((top1_right, picked_none))
        out[m] = {b: {"n": len(v), "top1_accuracy": (sum(1 for t, _ in v if t) / len(v)) if v else None,
                      "said_none": (sum(1 for _, n in v if n) / len(v)) if v else None} for b, v in bands.items()}
    return out


def position_bias(ds: str, cands: dict, eval_qids: list[str], normal: str = "jev-choice", reversed_: str = "jev-choice-reversed") -> dict | None:
    """Same 30 passages sent in reverse order: does the answer change?"""
    a, b = load_run(normal, ds, "present"), load_run(reversed_, ds, "present")
    both = [q for q in eval_qids if q in a and q in b and a[q]["ok"] and b[q]["ok"]]
    if not both:
        return None
    same_top1 = sum(1 for q in both if order(a[q])[0] == order(b[q])[0])
    nd_a = statistics.mean(ndcg(order(a[q]), cands[q]["relevant"]) for q in both)
    nd_b = statistics.mean(ndcg(order(b[q]), cands[q]["relevant"]) for q in both)
    mean_abs = statistics.mean(abs(x - y) for q in both for x, y in zip(a[q]["scores"], b[q]["scores"]))
    none_diff = statistics.mean(abs(a[q]["extra"]["none_prob"] - b[q]["extra"]["none_prob"]) for q in both) if "none_prob" in a[both[0]].get("extra", {}) else None
    return {"n": len(both), "same_top1_share": same_top1 / len(both), "ndcg10_normal": nd_a, "ndcg10_reversed": nd_b,
            "mean_abs_prob_diff": mean_abs, "mean_abs_none_prob_diff": none_diff}


def fmt(x, nd=3):
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{nd}f}"


def overall(res: dict, only: tuple[str, ...] | None = None) -> dict:
    """Macro-average over the datasets a model has run on (the table says how many), for the TL;DR.
    `only` restricts the average to a subset of datasets (the English-only headline)."""
    out = {}
    for m in MODELS:
        runs = [(d, r["models"][m]) for d, r in res["datasets"].items() if m in r["models"] and (only is None or d in only)]
        if not runs:
            continue
        def mean_of(key, sub=None):
            vals = []
            for _, r in runs:
                v = r.get(key) if sub is None else r.get(key, {}).get("signals", {}).get("max_score", {}).get(sub) if key == "nothing_relevant" else r.get(key, {}).get(sub)
                if v is not None and not (isinstance(v, float) and math.isnan(v)):
                    vals.append(v)
            return statistics.mean(vals) if vals else None
        out[m] = {"datasets": [d for d, _ in runs], "ndcg10": mean_of("ndcg10"), "top1": mean_of("top1"), "recall5": mean_of("recall5"),
                  "ndcg10_ties_against": mean_of("ndcg10_ties_against"), "tied_top_share": mean_of("tied_top_share"), "zero_score_share": mean_of("zero_score_share"), "saturated_share": mean_of("saturated_share"),
                  "call_ms_median": mean_of("call_ms_median"), "call_ms_p95": mean_of("call_ms_p95"), "query_ms_median": mean_of("query_ms_median"),
                  "cost_per_1k_queries": mean_of("cost_per_1k_queries"), "none_auroc": mean_of("nothing_relevant", "auroc"),
                  "none_false_accept": mean_of("nothing_relevant", "false_accept_rate"), "ece": mean_of("calibration", "ece")}
    return out


def markdown(res: dict) -> str:
    L = ["# Results", ""]
    L.append("Ranking numbers are over queries whose BM25 top-30 contains at least one relevant passage. "
             "Latency = one HTTP round trip from Algiers, all calls of both variants. Cost = the API's own usage field × list price "
             "(OpenRouter reports the exact billed amount), per 1,000 queries of 30 candidates.")
    for title, ov in (("TL;DR, English (average over the English datasets each model ran on)", res.get("overall_english") or {}),
                      ("All datasets including French", res.get("overall") or {})):
        if not ov:
            continue
        L += ["", f"## {title}", "",
              "| Model | datasets | nDCG@10 | Top-1 | median ms/call | median ms/query | $ per 1k queries | nothing-relevant AUROC | false accept @90% | ECE |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for m, r in ov.items():
            L.append(f"| {LABELS[m]} | {len(r['datasets'])} | {fmt(r['ndcg10'])} | {fmt(r['top1'])} | {fmt(r['call_ms_median'], 0)} | {fmt(r['query_ms_median'], 0)} | "
                     f"{fmt(r['cost_per_1k_queries'], 2)} | {fmt(r['none_auroc'])} | {fmt(r['none_false_accept'])} | {fmt(r['ece']) if m in PROB_MODELS else '—'} |")
    for ds, d in res["datasets"].items():
        L += ["", f"## {ds}", "", f"{d['queries_total']} queries; {d['queries_with_answer_in_top30']} have an answer in BM25's top 30 and are scored.", "",
              "| Model | n | nDCG@10 | Top-1 | Recall@5 | MRR@10 | calls | median ms/call | p95 ms/call | median ms/query | $ per 1k queries | none-test AUROC | false accept @90% | ECE |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for m, r in d["models"].items():
            nr = r.get("nothing_relevant", {}).get("signals", {}).get("max_score", {})
            cal = r.get("calibration", {})
            L.append(f"| {LABELS[m]} | {r['n']} | {fmt(r['ndcg10'])} | {fmt(r['top1'])} | {fmt(r['recall5'])} | {fmt(r['mrr10'])} | {r['calls']} | "
                     f"{fmt(r['call_ms_median'], 0)} | {fmt(r['call_ms_p95'], 0)} | {fmt(r['query_ms_median'], 0)} | "
                     f"{fmt(r['cost_per_1k_queries'], 2) if r['cost_per_1k_queries'] is not None else '—'} | {fmt(nr.get('auroc'))} | "
                     f"{fmt(nr.get('false_accept_rate'))} | {fmt(cal.get('ece')) + ('' if cal.get('is_probability_claim') else '*') if cal else '—'} |")
        extra = [(m, r["nothing_relevant"]["signals"]) for m, r in d["models"].items() if m == "jev-choice" and "nothing_relevant" in r]
        for m, sig in extra:
            L += ["", f"Jev Choice's own nothing-relevant signals ({ds}):", "", "| signal | AUROC | false accept @90% | median with answer | median without |", "|---|---|---|---|---|"]
            for name, s in sig.items():
                L.append(f"| {name} | {fmt(s['auroc'])} | {fmt(s['false_accept_rate'])} | {fmt(s['median_present'])} | {fmt(s['median_absent'])} |")
        for m, bands in (d.get("thresholds") or {}).items():
            L += ["", f"TypeSafe's confidence bands on real data, {LABELS[m]} ({ds}), queries that do have an answer in the 30:", "",
                  "| confidence | n | top pick is right | said none |", "|---|---|---|---|"]
            for b, v in bands.items():
                L.append(f"| {b} | {v['n']} | {fmt(v['top1_accuracy'])} | {fmt(v['said_none'])} |")
        pb = d.get("position_bias")
        if pb:
            L += ["", f"Position bias ({ds}): the same 30 passages sent in reverse order to Jev Choice. Same top pick {pb['same_top1_share']:.0%} of the time "
                  f"(n={pb['n']}); nDCG@10 {pb['ndcg10_normal']:.3f} normal vs {pb['ndcg10_reversed']:.3f} reversed; mean probability shift per passage "
                  f"{pb['mean_abs_prob_diff']:.3f}; P(none) shift {pb['mean_abs_none_prob_diff']:.3f}."]
    L += ["", "ECE marked * is for scores the vendor does not present as probabilities (shown for completeness, not held against them).", ""]
    # Usage totals per model, so every cost can be checked against the vendor dashboard.
    L += ["## Usage totals (check these against each vendor's dashboard)", "", "| Model | dataset | calls | usage | $ all variants |", "|---|---|---|---|---|"]
    for ds, d in res["datasets"].items():
        for m, r in d["models"].items():
            if r["calls"]:
                u = ", ".join(f"{k}={int(v) if float(v).is_integer() else round(v, 2)}" for k, v in r["usage_totals"].items())
                L.append(f"| {LABELS[m]} | {ds} | {r['calls']} | {u} | {r['cost_usd_all_variants']:.4f} |")
    return "\n".join(L)


def charts(res: dict) -> None:
    dsets = list(res["datasets"])
    present_models = [m for m in MODELS if any(m in res["datasets"][d]["models"] for d in dsets)]
    # Quality
    fig, ax = plt.subplots(figsize=(11, 4.5))
    w = 0.8 / max(1, len(present_models))
    for i, m in enumerate(present_models):
        ys = [res["datasets"][d]["models"].get(m, {}).get("ndcg10", 0) for d in dsets]
        ax.bar([x + i * w for x in range(len(dsets))], ys, w, label=LABELS[m])
    ax.set_xticks([x + 0.4 - w / 2 for x in range(len(dsets))]); ax.set_xticklabels(dsets); ax.set_ylabel("nDCG@10"); ax.set_ylim(0, 1)
    ax.legend(fontsize=7, ncol=3); ax.set_title("Ranking quality (higher is better)"); fig.tight_layout(); fig.savefig(RESULTS / "quality.png", dpi=150); plt.close(fig)
    # Calibration per dataset
    for d in dsets:
        fig, ax = plt.subplots(figsize=(5.5, 5))
        ax.plot([0, 1], [0, 1], "k--", lw=1, label="perfect")
        for m in present_models:
            cal = res["datasets"][d]["models"].get(m, {}).get("calibration")
            if not cal:
                continue
            pts = [(b["mean_score"], b["frac_relevant"]) for b in cal["bins"] if b["n"] >= 20]
            if pts:
                ax.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", label=f"{LABELS[m]} (ECE {cal['ece']:.2f})", alpha=0.85)
        ax.set_xlabel("score the model gave"); ax.set_ylabel("share that was actually relevant"); ax.set_title(f"Calibration, {d}")
        ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(RESULTS / f"calibration_{d}.png", dpi=150); plt.close(fig)
    # Nothing-relevant AUROC
    fig, ax = plt.subplots(figsize=(11, 4))
    for i, m in enumerate(present_models):
        ys = [res["datasets"][d]["models"].get(m, {}).get("nothing_relevant", {}).get("signals", {}).get("max_score", {}).get("auroc", 0) or 0 for d in dsets]
        ax.bar([x + i * w for x in range(len(dsets))], ys, w, label=LABELS[m])
    ax.axhline(0.5, color="k", lw=0.8, ls=":"); ax.set_xticks([x + 0.4 - w / 2 for x in range(len(dsets))]); ax.set_xticklabels(dsets)
    ax.set_ylim(0.4, 1); ax.set_ylabel("AUROC"); ax.set_title("Does the top score drop when the answer is removed? (1.0 = always, 0.5 = never)")
    ax.legend(fontsize=7, ncol=3); fig.tight_layout(); fig.savefig(RESULTS / "nothing_relevant.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    RESULTS.mkdir(exist_ok=True)
    res = evaluate()
    res["overall"] = overall(res)
    res["overall_english"] = overall(res, ENGLISH)
    (RESULTS / "summary.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    md = markdown(res)
    (RESULTS / "summary.md").write_text(md, encoding="utf-8")
    charts(res)
    print(md)
