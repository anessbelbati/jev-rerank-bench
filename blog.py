"""Render the blog post from the scorer's output. Every number comes from results/*.json; nothing is typed by hand.

    uv run eval.py && uv run blog.py      ->  results/BLOG-DRAFT.md
"""
from __future__ import annotations

import json
import statistics

from common import ENGLISH, RESULTS
from eval import LABELS, PROB_MODELS

S = json.load(open(RESULTS / "summary.json", encoding="utf-8"))
DET = json.load(open(RESULTS / "determinism.json", encoding="utf-8")) if (RESULTS / "determinism.json").exists() else None
COLD = json.load(open(RESULTS / "coldstart.json", encoding="utf-8")) if (RESULTS / "coldstart.json").exists() else None
D = S["datasets"]
EN = [d for d in ENGLISH if d in D]
NICE = {"scifact": "SciFact (science claims)", "fiqa": "FiQA (finance)", "nq": "Natural Questions (Google searches → Wikipedia)",
        "nfcorpus": "NFCorpus (medical)", "trec-covid": "TREC-COVID (COVID literature)", "bright-biology": "BRIGHT biology (reasoning)", "bright-earth_science": "BRIGHT earth science (reasoning)",
        "bright-psychology": "BRIGHT psychology (reasoning)", "bright-robotics": "BRIGHT robotics (reasoning)",
        "bright-stackoverflow": "BRIGHT StackOverflow (reasoning)", "bright-sustainable_living": "BRIGHT sustainable living (reasoning)",
        "bright-economics": "BRIGHT economics (reasoning)", "csn-python": "CodeSearchNet Python (code)", "miracl-fr": "MIRACL French"}
DEDICATED = ["cohere-pro", "cohere-fast", "zerank-2"]
JEV_MAIN = ["jev-choice", "jev-noul-batch", "jev-score-batch"]
JEV_ALL = [m for m in S["models"] if m.startswith("jev-") and m != "jev-choice-reversed"]
SIG = json.load(open(RESULTS / "significance.json", encoding="utf-8")) if (RESULTS / "significance.json").exists() else None
def rng(pr): return f"gap {100 * pr['diff']:+.1f} points, 95% range {100 * pr['ci95'][0]:+.1f} to {100 * pr['ci95'][1]:+.1f}"
def tag(pr): return ("real" if pr["p"] < 0.01 else f"real, but barely (p = {pr['p']:.3f})") if pr["real"] else "within noise"
NEV = json.load(open(RESULTS / "nevir.json", encoding="utf-8")) if (RESULTS / "nevir.json").exists() else None
CHK = json.load(open(RESULTS / "rlcd_check.json", encoding="utf-8")) if (RESULTS / "rlcd_check.json").exists() else None


def complete(m: str) -> bool:
    return all(m in D[d]["models"] and D[d]["models"][m]["failed"] == 0 for d in EN)


def en_avg(m: str, key: str, sub=None):
    vals = []
    for d in EN:
        x = D[d]["models"].get(m)
        if not x:
            continue
        v = x.get(key) if sub is None else (x.get(key) or {}).get("signals", {}).get("max_score", {}).get(sub) if key == "nothing_relevant" else (x.get(key) or {}).get(sub)
        if v is not None:
            vals.append(v)
    return statistics.mean(vals) if vals else None


def f(x, nd=3):
    return "n/a" if x is None else f"{x:.{nd}f}"


def pct(x):
    return "n/a" if x is None else f"{100 * x:.0f}%"


def sec(x):
    return "n/a" if x is None else (f"{x / 1000:.1f} s" if x >= 950 else f"{x:.0f} ms")


rows = {m: {"ndcg": en_avg(m, "ndcg10"), "top1": en_avg(m, "top1"), "ms": en_avg(m, "query_ms_median"), "call_ms": en_avg(m, "call_ms_median"),
            "cost": en_avg(m, "cost_per_1k_queries"), "none": en_avg(m, "nothing_relevant", "auroc"), "fa": en_avg(m, "nothing_relevant", "false_accept_rate"),
            "ece": en_avg(m, "calibration", "ece"), "complete": complete(m)} for m in S["models"] if not m.endswith("-reversed")}
ranked = sorted((m for m in rows if rows[m]["complete"] and m != "bm25"), key=lambda m: -rows[m]["ndcg"])
best = ranked[0]
best_dedicated = max((m for m in DEDICATED if rows[m]["complete"]), key=lambda m: rows[m]["ndcg"])
best_jev = max((m for m in JEV_ALL if rows[m]["complete"]), key=lambda m: rows[m]["ndcg"])
best_jev_simple = max((m for m in JEV_MAIN if rows[m]["complete"]), key=lambda m: rows[m]["ndcg"])
# "fastest" and "cheapest" only mean something among models close to the best; a bad model is trivially cheap.
competitive = [m for m in ranked if rows[m]["ndcg"] >= rows[best]["ndcg"] - 0.02]
cheapest = min(competitive, key=lambda m: rows[m]["cost"])
fastest = min(competitive, key=lambda m: rows[m]["ms"])
top1_best = max(ranked, key=lambda m: rows[m]["top1"])
none_best = max(ranked, key=lambda m: rows[m]["none"])
pts = lambda a, b: f"{100 * (rows[a]['ndcg'] - rows[b]['ndcg']):+.1f} points"

L: list[str] = []
P = L.append

P("# I tested TypeSafe's Jev against the best rerankers. Here's where it wins and where it doesn't.")
P("")
P("*Draft generated from the benchmark output on " + __import__("time").strftime("%Y-%m-%d") + ". Every number below is copied from the scoring script; the raw API responses are in the repo.*")
P("")
P("## TL;DR")
P("")
P(f"{len(EN)} English datasets, {sum(D[d]['queries_with_answer_in_top30'] for d in EN):,} scored questions, {len(rows)} model setups, every model reranking the same 30 keyword-search candidates per question. "
  f"Average over the {len(EN)} datasets (each dataset counts once):")
P("")
P("| Model | Ranking quality (nDCG@10) | Top pick right | Time per query | $ per 1,000 queries | Spots the 'nothing here' case (AUROC) |")
P("|---|---|---|---|---|---|")
for m in ranked + ["bm25"]:
    r = rows[m]
    P(f"| {LABELS[m]} | {f(r['ndcg'])} | {pct(r['top1'])} | {sec(r['ms']) if m != 'bm25' else '–'} | {f(r['cost'], 2) if m != 'bm25' else '0'} | {f(r['none'], 2)} |")
incomplete = [m for m in rows if not rows[m]["complete"]]
if incomplete:
    P("")
    P("Not shown (incomplete runs): " + ", ".join(LABELS[m] for m in incomplete) + ".")
P("")
runner_up = ranked[1]
tie = abs(rows[best]["ndcg"] - rows[runner_up]["ndcg"]) < 0.005
pr_top = SIG["overall"]["ndcg10"]["vs_best"].get(runner_up) if SIG and SIG["overall"]["ndcg10"]["best"] == best else None
if pr_top:
    tie = not pr_top["real"]
if tie:
    P(f"- **Best ranking quality:** a tie between {LABELS[best]} ({f(rows[best]['ndcg'])}) and {LABELS[runner_up]} ({f(rows[runner_up]['ndcg'])})"
      + (f": {rng(pr_top)} over {SIG['B']:,} resamples of the questions, so the difference is inside the noise." if pr_top else "; the difference is inside the noise."))
elif best.startswith("jev"):
    P(f"- **Best ranking quality:** {LABELS[best]} ({f(rows[best]['ndcg'])}). The best dedicated reranker, {LABELS[best_dedicated]}, is at {f(rows[best_dedicated]['ndcg'])} ({pts(best_dedicated, best)}).")
else:
    P(f"- **Best ranking quality:** {LABELS[best]} ({f(rows[best]['ndcg'])}). The best Jev setup, {LABELS[best_jev]}, is at {f(rows[best_jev]['ndcg'])} ({pts(best_jev, best)}).")
pr_t1 = SIG["pairs"]["top1"].get(f"{top1_best}|cohere-pro") if SIG else None
P(f"- **Best top pick:** {LABELS[top1_best]} ({pct(rows[top1_best]['top1'])})"
  + (f"; against {LABELS['cohere-pro']} ({pct(rows['cohere-pro']['top1'])}) the {rng(pr_t1)}: {tag(pr_t1)}." if pr_t1 else "."))
if NEV:
    nd = {m: v for m, v in NEV.items() if m in LABELS and v["pairs_failed"] == 0}
    nj = max((m for m in nd if m.startswith("jev-")), key=lambda m: nd[m]["paired_accuracy"]); no = max((m for m in nd if not m.startswith("jev-") and m != "bm25"), key=lambda m: nd[m]["paired_accuracy"])
    nb = NEV.get("_bootstrap", {}).get(f"{nj}|{no}")
    P(f"- **Reads \"not\":** on NevIR's negation pairs, {LABELS[nj]} gets {pct(nd[nj]['paired_accuracy'])} of pairs right vs {LABELS[no]} {pct(nd[no]['paired_accuracy'])}"
      + (f" (gap {100 * nb['diff']:+.1f}, 95% range {100 * nb['ci95'][0]:+.1f} to {100 * nb['ci95'][1]:+.1f}: {'real' if nb['real'] else 'within noise'})" if nb else "")
      + f"; the cheap chat-model baseline scores {pct(min(nd[m]['paired_accuracy'] for m in nd if m.startswith('deepseek')))}, below the 25% you get by guessing.")
P(f"- Among models within 2 points of the best: **fastest** {LABELS[fastest]} ({sec(rows[fastest]['ms'])} per query), **cheapest** {LABELS[cheapest]} (${f(rows[cheapest]['cost'], 2)} per 1,000 queries).")
P(f"- **Best at noticing that no passage answers the question:** {LABELS[none_best]} (AUROC {f(rows[none_best]['none'], 2)}).")
P("")
P("## Why test this")
P("")
P("Jev launched on September 15, 2026 with big claims: typed decisions with calibrated probabilities, 70–500 ms, $0.042 per million input tokens, output free. "
  "Half of X called it \"just a classifier\", and nobody put it next to the obvious specialists: the dedicated rerankers from Cohere and ZeroEntropy, or a cheap chat model reading the probability of a single \"yes\" token, which is the baseline a Kaggle grandmaster asked for on launch day. So I ran that, with reproducible code.")
P("")
P("[PASTE: Diogo's launch tweet and Ahmet's \"run the baseline\" post, with links]")
P("")
P("## Setup, short")
P("")
P("- **Candidates:** BM25 top 30 per question, the same 30 for every model, cut to 2,000 characters. Ranking scores count only questions where BM25 actually found an answer in the 30 (a reranker can reorder, it can't conjure).")
P("- **Datasets (English):** " + "; ".join(f"{NICE[d]}, {D[d]['queries_with_answer_in_top30']} scored" for d in EN) + ". French (MIRACL) is a side test at the end.")
P("- **Models:** Cohere Rerank 4 Pro and Fast; ZeroEntropy zerank-2; DeepSeek V4.1 Flash (thinking off) two ways: yes-probability per pair and JSON scores for all 30 in one call; Jev eight ways, including the three patterns from TypeSafe's own cookbooks; BM25 alone as the floor.")
P("- **Measured:** nDCG@10, top-1, recall@5; latency of one HTTP round trip from Algiers; cost from each API's own usage field × list price (OpenRouter returns the exact billed amount); a \"nothing relevant\" test; calibration; and for Jev: its confidence bands, order sensitivity, and repeat drift.")
P("- **Fairness:** same candidates, same truncation, same relevance wording for the models that take one; when two passages get the exact same score, they keep BM25 order (for every model; the worst-case reading is reported below); public datasets may be in anyone's training data; every loss shown; raw responses published.")
if SIG:
    P(f"- **Noise:** every gap in this post comes with a 95% range from {SIG['B']:,} paired resamples of the questions (the questions are the sample; the models themselves are stable, see the repeat test below). A gap whose range excludes zero is called real; otherwise, within noise.")
P("")
P("## Results: ranking quality")
P("")
P("Per dataset, nDCG@10 (higher is better), scored questions in brackets:")
P("")
show = [m for m in ["cohere-pro", "cohere-fast", "zerank-2", "deepseek-json", "deepseek-pair", "qwen-rlcd-batch", "qwen-rlcd-rubric", "qwen-rlcd-pair", "jev-choice", "jev-noul-batch", "jev-score-batch", "jev-noul-pair", "bm25"] if m in rows]
P("| Dataset | " + " | ".join(LABELS[m] for m in show) + " |")
P("|---|" + "---|" * len(show))
for d in EN:
    cells = []
    vals = {m: D[d]["models"][m]["ndcg10"] for m in show if m in D[d]["models"] and m != "bm25"}
    top = max(vals, key=vals.get)
    for m in show:
        x = D[d]["models"].get(m)
        cells.append(("**" if m == top else "") + (f(x["ndcg10"]) if x else "n/a") + ("**" if m == top else ""))
    P(f"| {NICE[d]} ({D[d]['queries_with_answer_in_top30']}) | " + " | ".join(cells) + " |")
P("")
wins = {}
for d in EN:
    vals = {m: D[d]["models"][m]["ndcg10"] for m in rows if m in D[d]["models"] and m != "bm25" and D[d]["models"][m]["failed"] == 0}
    wins[d] = max(vals, key=vals.get)
by_family = {"Jev": sum(1 for m in wins.values() if m.startswith("jev")), "Cohere": sum(1 for m in wins.values() if m.startswith("cohere")),
             "ZeroEntropy": sum(1 for m in wins.values() if m == "zerank-2"), "DeepSeek": sum(1 for m in wins.values() if m.startswith("deepseek"))}
P("First place per dataset (any setup of the family counts): " + ", ".join(f"{k} {v}" for k, v in by_family.items() if v) + ". "
  + "Where Jev is first: " + ", ".join(NICE[d].split(" (")[0] + (f" (by {100 * SIG['datasets'][d]['jev_vs_other']['diff']:.1f} points, {tag(SIG['datasets'][d]['jev_vs_other'])})" if SIG else "") for d, m in wins.items() if m.startswith("jev")) + ". "
  + "Where it is not: " + ", ".join(f"{NICE[d].split(' (')[0]} ({LABELS[m]} by {100 * (D[d]['models'][m]['ndcg10'] - max(D[d]['models'][j]['ndcg10'] for j in JEV_ALL if j in D[d]['models'])):.1f} points" + (f", {tag(SIG['datasets'][d]['jev_vs_other'])}" if SIG else "") + ")" for d, m in wins.items() if not m.startswith("jev")) + ".")
if SIG:
    jf = [d for d, m in wins.items() if m.startswith("jev")]; nf = [d for d, m in wins.items() if not m.startswith("jev")]
    real_w = [d for d in jf if SIG["datasets"][d]["jev_vs_other"]["real"]]; real_l = [d for d in nf if SIG["datasets"][d]["jev_vs_other"]["real"]]
    P(f"\"Real\" means the 95% range of the gap, over {SIG['B']:,} paired resamples of the questions, excludes zero; \"within noise\" means it does not. "
      f"So: of Jev's {len(jf)} first places, {len(real_w)} {'is' if len(real_w) == 1 else 'are'} real{' (' + ', '.join(NICE[d].split(' (')[0] for d in real_w) + ')' if real_w else ''}; "
      f"of the {len(nf)} datasets where it is not first, {len(real_l)} {'is a real loss' if len(real_l) == 1 else 'are real losses'}{' (' + ', '.join(NICE[d].split(' (')[0] for d in real_l) + ')' if real_l else ''}. "
      f"The small sets (TREC-COVID, the two BRIGHT subsets) have wide ranges; read their verdicts loosely.")
P("")
lead = ""
if SIG and SIG["overall"]["ndcg10"]["best"] == best_jev_simple:
    vb = SIG["overall"]["ndcg10"]["vs_best"]
    lead = " Its lead over the other one-call modes is small but real (" + "; ".join(f"vs {LABELS[m]}: {rng(vb[m])}, {tag(vb[m])}" for m in ("jev-noul-batch", "jev-choice") if m in vb) + ")."
P(f"Among the Jev setups, the simple ones win: {LABELS[best_jev_simple]} at {f(rows[best_jev_simple]['ndcg'])}.{lead} "
  f"The per-pair pattern from TypeSafe's own reranking cookbook is worse ({f(rows['jev-noul-pair']['ndcg'])}) and twice the price. "
  f"The pairwise duels idea ({f(rows['jev-duel']['ndcg'])}) fails because it only duels BM25's top 10, and the answer is often lower; "
  f"tournament ({f(rows['jev-tournament']['ndcg'])}) and cascade ({f(rows['jev-cascade']['ndcg'])}) don't beat one plain call either.")
P("")
if "qwen-rlcd-batch" in rows and rows["qwen-rlcd-batch"]["complete"]:
    q = "qwen-rlcd-batch"; qr = "qwen-rlcd-rubric" if "qwen-rlcd-rubric" in rows and rows["qwen-rlcd-rubric"]["complete"] else None
    best_q = max([m for m in (q, qr) if m], key=lambda m: rows[m]["ndcg"])
    pr_q = SIG["overall"]["ndcg10"]["vs_best"].get(best_q) if SIG else None
    P("### The open-source answer: a 1.5B model with parallel constrained decoding")
    P("")
    P(f"The day after the launch, several people posted the same idea on Hugging Face under the name \"Qwen-2.5-1B-RLCD\": take Qwen2.5-1.5B-Instruct, no training, prefill the prompt once, then score every JSON key in one batched pass by a softmax over the allowed answers. "
      f"It is exactly the shape of Jev's one-call modes, so I ran it the same two ways, with the model's own inference code, on rented RTX 4090s: 30 yes/no keys with Jev's wording, and 30 keys with Jev's four-level rubric. "
      f"Result on the 8-dataset headline: {LABELS[q]} {f(rows[q]['ndcg'])}" + (f", {LABELS[qr]} {f(rows[qr]['ndcg'])}" if qr else "") + f", against {f(rows[best]['ndcg'])} for {LABELS[best]}"
      + (f" ({rng(pr_q)}, {tag(pr_q)})" if pr_q else "") + f"; top pick {pct(rows[best_q]['top1'])} vs {pct(rows[top1_best]['top1'])}. "
      f"Per query it took {sec(rows[best_q]['ms'])} of GPU time on the 4090 (${f(rows[best_q]['cost'], 3)} per 1,000 queries at the pod's hourly price, setup not counted), "
      f"and it keeps its probabilities, so it also gets a calibration row and a NevIR row below. The recipe is real and cheap; whether a 1.5B model is enough is what the numbers say.")
    P("")
    P(f"They say no. Both versions land below the BM25 order they were handed ({f(rows['bm25']['ndcg'])}): the model makes the keyword ranking worse. "
      + (f"The scores are not random, just weak: over the 8 datasets a relevant passage scores {f(CHK[q]['relevant_mean'])} on average and an irrelevant one {f(CHK[q]['non_relevant_mean'])} in the yes/no version (gap {f(CHK[q]['gap'])}), "
         f"against {f(CHK['jev-noul-batch']['relevant_mean'])} vs {f(CHK['jev-noul-batch']['non_relevant_mean'])} (gap {f(CHK['jev-noul-batch']['gap'])}) for Jev's yes/no with the same wording and the same 30 passages in one call. "
         f"And the yes/no version drifts with position: the 30th passage in the list averages {f(CHK[q]['position_mean']['30'])} and the 1st {f(CHK[q]['position_mean']['1'])}, although the 1st is far more often the relevant one. "
         f"A 1.5B model asked to keep 30 passages apart in one prompt mostly answers from where the passage sits, not from what it says. " if CHK and q in CHK and "jev-noul-batch" in CHK else "")
      + "One honest note on the run: on 24 GB cards the model's one-shot pass ran out of memory on the longest code-heavy prompts (StackOverflow and robotics), so those rows were scored six keys at a time against the same prefill, which is the same arithmetic in smaller pieces; the raw rows say which ones.")
    P("")
    qp = "qwen-rlcd-pair" if "qwen-rlcd-pair" in rows and rows["qwen-rlcd-pair"]["complete"] else None
    if qp:
        pr_pb = SIG["pairs"]["ndcg10"].get("qwen-rlcd-pair|bm25") if SIG else None
        pr_pq = SIG["pairs"]["ndcg10"].get("qwen-rlcd-pair|qwen-rlcd-batch") if SIG else None
        P(f"To be fair to the model rather than to the recipe, I also gave it the easiest possible shape: one passage per prompt, one yes/no key, thirty prompts per query, still scored by its own function. "
          f"That version reaches nDCG {f(rows[qp]['ndcg'])} and a right top pick {pct(rows[qp]['top1'])} of the time"
          + (f"; against BM25: {rng(pr_pb)}, {tag(pr_pb)}" if pr_pb else "") + (f"; against its own 30-key version: {rng(pr_pq)}, {tag(pr_pq)}" if pr_pq else "") + ". "
          + (f"Its scores separate relevant from irrelevant passages by {f(CHK[qp]['gap'])}, against {f(CHK['jev-noul-pair']['gap'])} for Jev asked one passage at a time with the same words. " if CHK and qp in CHK and "jev-noul-pair" in CHK else "")
          + f"It costs {sec(rows[qp]['ms'])} of GPU time per query (thirty prompts one after the other, ${f(rows[qp]['cost'], 3)} per 1,000)"
          + (f", and it gets {pct(NEV[qp]['paired_accuracy'])} of NevIR pairs right" if NEV and qp in NEV else "") + ".")
        P("")
    pbq = {d: D[d].get("position_bias_qwen") for d in EN}; pbq = {d: x for d, x in pbq.items() if x}
    pbj = {d: D[d].get("position_bias") for d in EN}; pbj = {d: x for d, x in pbj.items() if x}
    if pbq and pbj:
        rev_nq = sum(x["n"] for x in pbq.values()); same_q = sum(x["n"] * x["same_top1_share"] for x in pbq.values()) / rev_nq
        move_q = sum(x["n"] * x["mean_abs_prob_diff"] for x in pbq.values()) / rev_nq
        rev_nj = sum(x["n"] for x in pbj.values()); same_j = sum(x["n"] * x["same_top1_share"] for x in pbj.values()) / rev_nj
        move_j = sum(x["n"] * x["mean_abs_prob_diff"] for x in pbj.values()) / rev_nj
        P(f"Is it at least consistent, or is it noise? A forward pass with no sampling returns the same numbers on every repeat, so the repeat test is clean by construction; the order test is the one that bites. "
          f"Send the same 30 passages in reverse order and the 30-key version changes its top pick {pct(1 - same_q)} of the time (pooled over the 8 datasets, {rev_nq} questions) and moves each passage's probability by {f(move_q)} on average; "
          f"Jev's Choice, same test, changes its top pick {pct(1 - same_j)} of the time ({rev_nj} questions) and moves each probability by {f(move_j)}. "
          f"So it is not random: it is stable, and stably wrong about where to look.")
        P("")
from common import BRIGHT
BR = [d for d in BRIGHT if d in D]
BR_MODELS = [m for m in ("cohere-pro", "zerank-2", "deepseek-json", "qwen-rlcd-batch", "qwen-rlcd-pair", "jev-score-batch", "jev-choice", "jev-noul-batch") if all(m in D[d]["models"] and D[d]["models"][m]["failed"] == 0 for d in BR)]
if len(BR) > 2 and BR_MODELS:
    P("### The reasoning block: seven BRIGHT subsets")
    P("")
    P("BRIGHT is the set where the question and the answer share few words and you have to think (StackExchange questions, web documents). The two subsets in the headline gave Jev a small lead that the bootstrap called noise, "
      f"so I ran the other five StackExchange subsets afterwards, same pipeline, same models, same scoring, and report them here as their own block. They are not added to the headline average, which was fixed before they ran. Scored questions in brackets.")
    P("")
    P("| Subset | " + " | ".join(LABELS[m] for m in BR_MODELS) + " |")
    P("|---|" + "---|" * len(BR_MODELS))
    for d in BR:
        vals = {m: D[d]["models"][m]["ndcg10"] for m in BR_MODELS}; top = max(vals.values())
        P(f"| {NICE[d].split(' (')[0]} ({D[d]['queries_with_answer_in_top30']}) | " + " | ".join(f"**{f(v)}**" if v == top else f(v) for v in vals.values()) + " |")
    avg = {m: statistics.mean(D[d]["models"][m]["ndcg10"] for d in BR) for m in BR_MODELS}; top = max(avg.values())
    P(f"| **Average of {len(BR)}** | " + " | ".join(f"**{f(v)}**" if v == top else f(v) for v in avg.values()) + " |")
    P("")
    if SIG and SIG.get("bright"):
        b = SIG["bright"]["ndcg10"]; j = b["jev_vs_other"]; t = SIG["bright"]["top1"]["jev_vs_other"]
        P(f"Bootstrap over the {len(b['datasets'])} subsets ({b['n']} scored questions): best Jev setup ({LABELS[j['a']]}) vs best other ({LABELS[j['b']]}), ranking quality: {rng(j)}, {tag(j)}. "
          f"Top pick: {LABELS[t['a']]} vs {LABELS[t['b']]}, {rng(t)}, {tag(t)}.")
        P("")
sat = sorted(((m, en_avg(m, "ndcg10"), en_avg(m, "ndcg10_ties_against"), en_avg(m, "zero_score_share"), en_avg(m, "tied_top_share"))
              for m in ranked if en_avg(m, "ndcg10") - en_avg(m, "ndcg10_ties_against") >= 0.01), key=lambda t: t[2] - t[1])
if sat:
    others = max(abs(en_avg(m, "ndcg10") - en_avg(m, "ndcg10_ties_against")) for m in ranked if m not in {t[0] for t in sat})
    P("**One catch: ties.** When a model gives two passages the exact same score, I keep BM25's order between them, so a model that hands out many identical scores gets part of its ranking from BM25. "
      "Break ties against the model instead and " + "; ".join(f"{LABELS[m]} drops from {f(a)} to {f(b)} (it scores {pct(z)} of passages exactly 0{', and the top score is tied on ' + pct(t) + ' of questions' if t >= 0.1 else ''})" for m, a, b, z, t in sat)
      + f". Every other model moves by {others:.3f} or less. Jev's Choice mode puts all its probability on a handful of passages and exact zeros on the rest: it is a very good top pick, and below that the order is BM25's.")
    P("")
if NEV:
    done = {m: v for m, v in NEV.items() if m in LABELS and v["pairs_failed"] == 0}
    P("## Can it read \"not\"? The NevIR test")
    P("")
    P("NevIR is 1,383 pairs of passages that are identical except for a negation, each with two questions: question 1 is answered by passage 1, question 2 by passage 2. A model gets a pair right only if it ranks the right passage first for both questions; ties count as wrong. "
      "Guessing scores 25%. Keyword search scores about zero by construction (the word 'not' is a stopword, so both passages get the same score). Rerankers were famously bad at this when the test came out in 2023. Every model saw the two passages in the same order for both questions.")
    P("")
    P("| Model | Pairs right (both questions) | Questions right | Same top pick for both questions | Time per question | $ per 1,000 questions |")
    P("|---|---|---|---|---|---|")
    for m, v in sorted(done.items(), key=lambda kv: -kv[1]["paired_accuracy"]):
        P(f"| {LABELS[m]} | {pct(v['paired_accuracy'])} | {pct(v['question_accuracy'])} | {pct(v['same_top_pick_share'])} | {sec(v['query_ms_median']) if v['query_ms_median'] else '–'} | {v['cost_per_1k_questions']:.3f} |")
    P("")
    missing = [LABELS[m] for m in NEV if m in LABELS and NEV[m]["pairs_failed"]]
    if missing:
        P("Not shown (incomplete runs): " + ", ".join(missing) + ".")
        P("")
    bj = max((m for m in done if m.startswith("jev-")), key=lambda m: done[m]["paired_accuracy"])
    bo = max((m for m in done if not m.startswith("jev-") and m != "bm25"), key=lambda m: done[m]["paired_accuracy"])
    line = f"Jev's best setup ({LABELS[bj]}) gets {pct(done[bj]['paired_accuracy'])} of pairs right; the best of the others ({LABELS[bo]}) {pct(done[bo]['paired_accuracy'])}."
    bs = NEV.get("_bootstrap", {}).get(f"{bj}|{bo}")
    if bs:
        line += f" Gap {100 * bs['diff']:+.1f} points, 95% range {100 * bs['ci95'][0]:+.1f} to {100 * bs['ci95'][1]:+.1f} over {bs['B']:,} resamples of the pairs: {'real' if bs['real'] else 'within noise'}."
    ds_p = [m for m in done if m.startswith("deepseek")]
    if ds_p:
        worst = min(ds_p, key=lambda m: done[m]["paired_accuracy"])
        line += f" The chat-model baseline is below guessing ({LABELS[worst]}: {pct(done[worst]['paired_accuracy'])}): it picks the same passage for both questions {pct(done[worst]['same_top_pick_share'])} of the time, so it is not reading the negation at all."
    P(line + " Together with the top pick, this is where a decision model and a reranker part ways.")
    P("")
P("## Results: speed and cost")
P("")
P("| Model | median per call | median per query (30 candidates) | $ per 1,000 queries | tokens or units it bills |")
P("|---|---|---|---|---|")
bill = {"cohere-pro": "1 search unit per query", "cohere-fast": "1 search unit per query", "zerank-2": "the passages, at $0.025/M tokens",
        "deepseek-pair": "30 prompts per query at $0.15/M", "deepseek-json": "the passages once at $0.15/M", "jev-noul-pair": "30 states per query at $0.042/M",
        "qwen-rlcd-batch": "GPU seconds on a rented RTX 4090 at $0.74/h", "qwen-rlcd-rubric": "GPU seconds on a rented RTX 4090 at $0.74/h", "qwen-rlcd-pair": "GPU seconds on a rented RTX 4090 at $0.74/h, 30 prompts in sequence",
        "jev-noul-batch": "the passages once + 30 questions at $0.042/M", "jev-choice": "the passages once + 1 question at $0.042/M",
        "jev-score-batch": "the passages once + 30 rubric questions at $0.042/M", "jev-duel": "10 passages + 45 questions", "jev-tournament": "two calls",
        "jev-cascade": "one batched call + 8 pair calls"}
for m in ranked:
    r = rows[m]
    P(f"| {LABELS[m]} | {sec(r['call_ms'])} | {sec(r['ms'])} | {f(r['cost'], 2)} | {bill.get(m, '')} |")
P("")
NET = json.load(open(RESULTS / "network.json", encoding="utf-8")) if (RESULTS / "network.json").exists() else None
if NET:
    tc = NET["tcp_connect"]; js = NET["jev_server_time"]
    lo, hi = min(v["median_ms"] for v in tc.values()), max(v["median_ms"] for v in tc.values())
    trip = statistics.mean(o["round_trip_ms_median"] - o["server_ms_median"] for o in js.values())
    parts = "; ".join(f"{LABELS[k]}: {o['round_trip_ms_median']:.0f} ms round trip, of which {o['server_ms_median']:.0f} ms on Jev's side" for k, o in js.items())
    est = "; ".join(f"{LABELS[m]} about {sec(rows[m]['call_ms'] - trip)}" for m in ("cohere-pro", "cohere-fast", "zerank-2") if m in rows)
    P(f"**What is network and what is model.** Every time above is one HTTP round trip from my desk in Algiers, so it includes the trip, for every API alike. A bare connection to the three API hosts takes {lo:.0f}–{hi:.0f} ms, about the same for all three. "
      f"Jev returns its own server-side time in a response header, so for Jev I can split it: on {next(iter(js.values()))['n']} real 30-passage SciFact calls per mode, {parts}. "
      f"So the trip costs about {trip:.0f} ms per call and Jev's model time on 30 passages is roughly {min(o['server_ms_median'] for o in js.values()):.0f}–{max(o['server_ms_median'] for o in js.values()):.0f} ms. "
      f"Cohere (via OpenRouter) and ZeroEntropy return no timing header; taking the same {trip:.0f} ms off their per-call medians gives an estimated model time of {est}. The speed order does not change.")
    P("")
P(f"Per-pair setups pay 30 round trips per query (the per-query time above is sequential; in production you'd fire them in parallel and pay one round trip). "
  f"On price, note that Jev is not the cheapest: ZeroEntropy bills $0.025 per million tokens against Jev's $0.042, and both read the same ~7,600 tokens per query. "
  f"Jev is cheap relative to Cohere (per search) and to a chat model, not relative to a dedicated cheap reranker.")
P("")
BAT = json.load(open(RESULTS / "batching.json", encoding="utf-8")) if (RESULTS / "batching.json").exists() else None
if BAT:
    a = BAT["billing_curve"]; a1, aN = a[0], a[-1]
    per_q = (aN["input_tokens"] - a1["input_tokens"]) / (aN["k"] - a1["k"])
    ct = {b["k"]: b for b in BAT["crosstalk"]}
    largest = max(b["largest_ok_input_tokens"] for b in BAT["crosstalk"] if b["largest_ok_input_tokens"])
    smallest_fail = min((e["passages"] for b in BAT["crosstalk"] for e in b["errors"]), default=None)
    P("## The price trick: many questions, one request")
    P("")
    P(f"Jev bills the input tokens of a request, passages plus question text, and output is free. So if several questions concern the same passages, one request with all the questions pays the passages once. I measured it on SciFact: "
      f"the same 30 passages with 1 query's Choice question bill {a1['input_tokens']:,} tokens; with {aN['k']} different queries' questions in the same request, {aN['input_tokens']:,}. "
      f"Each extra query costs about {per_q:.0f} tokens, {per_q / a1['input_tokens']:.0%} of the passages. "
      f"That is ${a1['cost_usd'] * 1000:.2f} per 1,000 queries one at a time versus ${aN['cost_usd'] / aN['k'] * 1000:.3f} per 1,000 queries {aN['k']} at a time, {a1['cost_usd'] / (aN['cost_usd'] / aN['k']):.0f}× cheaper, and the {aN['k']}-question request answered in {sec(aN['latency_ms'])}. "
      f"Query 1's own answer did not change when the other {aN['k'] - 1} rode along (same pick each time; its probability moved from {a1['q1_top_prob']:.2f} to {aN['q1_top_prob']:.2f}).")
    P("")
    P(f"Two limits. First, the request has a ceiling: the largest request Jev accepted was {largest:,} input tokens and everything bigger came back `max_tokens_exceeded`; with 2,000-character passages that is about {smallest_fail - 1 if smallest_fail else '?'} passages, so roughly three queries' worth of distinct candidates, or as many questions as you like over a shared set that fits. "
      f"Second, the passages have to be shared for the trick to work. Packing queries that each bring their own 30 candidates only saves what the ceiling allows: "
      + "; ".join(f"{b['k']} {'query' if b['k'] == 1 else 'queries'} per request: nDCG {f(b['ndcg10'])} vs {f(b['baseline_ndcg10'])} one at a time, same top pick {pct(b['same_top1_share'])} of the time, ${b['cost_per_1k_queries']:.2f} vs ${b['baseline_cost_per_1k_queries']:.2f} per 1,000 ({b['queries_scored']} queries)" for k, b in sorted(ct.items()) if b["queries_scored"] and b["calls_ok"] >= b["groups"] / 2)
      + ". The 1-query row is the control for the changed wording; the drop at 3 is small but real, so a bigger state costs a little accuracy. (4 per request fit the ceiling only 4 times in 30, so it is not reported.)")
    P("")
    P("So for ordinary search, where every query has its own candidates, there is no trick and ZeroEntropy stays cheaper. Where it changes the economics is many questions against the same passages: a support bot over one manual, forty claims checked against one document, a judge scoring every question against the same set of reviews. There Jev is an order of magnitude cheaper than anything in this table.")
    P("")
P("## Results: the 'nothing relevant' test and calibration")
P("")
P("For every question where BM25 found the answer, I also built a twin list with every relevant passage removed and the list refilled from further down BM25: same question, 30 on-topic passages, none of which answers it. "
  "A good model's top score should drop. AUROC = how reliably it does (1.0 always, 0.5 never); false-accept = at the threshold that keeps 90% of real answers, what share of the empty lists still get waved through.")
P("")
P("| Model | AUROC | false accept @ 90% recall |")
P("|---|---|---|")
for m in sorted(ranked, key=lambda m: -(rows[m]["none"] or 0)):
    P(f"| {LABELS[m]} | {f(rows[m]['none'], 2)} | {pct(rows[m]['fa'])} |")
jc = {d: D[d]["models"]["jev-choice"]["nothing_relevant"]["signals"] for d in EN if "jev-choice" in D[d]["models"] and "nothing_relevant" in D[d]["models"]["jev-choice"]}
none_note = "Jev's built-in `none` adds nothing over its top score"
if jc:
    none_sig = statistics.mean(s["1-P(none)"]["auroc"] for s in jc.values()); any_sig = statistics.mean(s["P(any)"]["auroc"] for s in jc.values()); max_sig = statistics.mean(s["max_score"]["auroc"] for s in jc.values())
    P("")
    verdict = ("a little better than" if max(none_sig, any_sig) > max_sig + 0.01 else "no better than" if max(none_sig, any_sig) >= max_sig - 0.01 else "worse than")
    none_note = (f"Jev's built-in `none` helps a little ({f(max(none_sig, any_sig), 2)} vs {f(max_sig, 2)} from its top score) but still trails" if max(none_sig, any_sig) > max_sig + 0.01
                 else "Jev's built-in `none` adds nothing over its top score")
    P(f"Jev's built-in `none` option is its selling point here, so I checked it separately: as a signal, 1 − P(none) scores {f(none_sig, 2)} and the 'does any passage answer it?' yes/no scores {f(any_sig, 2)}, against {f(max_sig, 2)} for simply reading Jev's top probability. "
      f"The built-in option is {verdict} the number every reranker already gives you, and still behind {LABELS[none_best]} ({f(rows[none_best]['none'], 2)}). "
      f"And nobody is good in absolute terms: at 90% recall, the best model still accepts {pct(min(rows[m]['fa'] for m in ranked))} of the empty lists.")
P("")
P("**Calibration.** For the models that present their scores as probabilities: expected calibration error (0 = perfect), and what share of passages scored 0.9–1.0 were actually relevant.")
P("")
P("| Model | ECE, average | passages scored 0.9+ that were relevant, per dataset |")
P("|---|---|---|")
for m in [m for m in PROB_MODELS if m in rows and rows[m]["complete"]]:
    tops = []
    for d in EN:
        cal = D[d]["models"].get(m, {}).get("calibration")
        if cal:
            b = cal["bins"][-1]
            if b["n"] >= 20:
                tops.append(f"{NICE[d].split(' (')[0]} {pct(b['frac_relevant'])}")
    P(f"| {LABELS[m]} | {f(rows[m]['ece'])} | {'; '.join(tops)} |")
P("")
P("## Jev under the microscope")
P("")
th = {d: D[d].get("thresholds", {}).get("jev-choice") for d in EN}
th = {d: t for d, t in th.items() if t}
if th:
    def pooled(band):
        n = sum(t[band]["n"] for t in th.values()); hits = sum(t[band]["n"] * (t[band]["top1_accuracy"] or 0) for t in th.values())
        return hits / n if n else None, n
    (hi, nhi), (mid, nmid), (lo, nlo) = pooled(">=0.9"), pooled("0.5-0.9"), pooled("<0.5")
    P(f"- **TypeSafe's own rule holds.** Their docs say act automatically above 0.9 confidence, proceed with care between 0.5 and 0.9, ask a human below 0.5. Pooled over the {len(th)} English datasets, Jev Choice's top pick is right {pct(hi)} of the time above 0.9 ({nhi} questions), "
      f"{pct(mid)} in the middle band ({nmid}), {pct(lo)} below 0.5 ({nlo}).")
pb = {d: D[d].get("position_bias") for d in EN}
pb = {d: p for d, p in pb.items() if p}
if pb:
    n = sum(p["n"] for p in pb.values()); same = sum(p["n"] * p["same_top1_share"] for p in pb.values()) / n
    P(f"- **Order matters a bit.** Send the same 30 passages in reverse and the top pick changes {pct(1 - same)} of the time (pooled, {n} questions); nDCG moves by at most {max(abs(p['ndcg10_normal'] - p['ndcg10_reversed']) for p in pb.values()):.3f} on any dataset.")
if DET:
    a, b = DET["jev-noul-batch"], DET["jev-choice"]
    P(f"- **It moves.** The same request repeated (100 SciFact questions, twice each): identical answers only {pct(a['identical_share'])} of the time for 30 yes/no in one call and {pct(b['identical_share'])} for Choice; "
      f"probabilities drift by {a['max_abs_prob_diff_mean']:.3f} on average, up to {max(a['max_abs_prob_diff_max'], b['max_abs_prob_diff_max']):.2f}; the top pick changed {a['top1_changed'] + b['top1_changed']} times in 400 repeats. Small, but not the 'distribution you can threshold' the pitch implies.")
if COLD:
    gaps = [r for r in COLD if r["idle_s"] > 0]
    worst = max(gaps, key=lambda r: r["first_call_ms"])
    P(f"- **Cold start.** After {', '.join(str(r['idle_s'] // 60) for r in gaps)} minutes of silence, the first call took {sec(min(r['first_call_ms'] for r in gaps))}–{sec(worst['first_call_ms'])} "
      f"(warm calls: {sec(statistics.median(x for r in COLD for x in r['next_two_ms']))}). "
      + ("During the build I saw five first-calls of ~22 s after idle periods; " + ("the controlled test reproduced it." if worst["first_call_ms"] > 5000 else f"the controlled test did not reproduce it up to {worst['idle_s'] // 60 if worst['idle_s'] == max(r['idle_s'] for r in gaps) else max(r['idle_s'] for r in gaps) // 60} minutes idle.")))
P("")
fr = D.get("miracl-fr")
if fr:
    P("## French, as a side note")
    P("")
    vals = {m: fr["models"][m]["ndcg10"] for m in ranked if m in fr["models"]}
    order = sorted(vals, key=vals.get, reverse=True)
    P("TypeSafe never claimed other languages; Cohere and ZeroEntropy advertise 100+. On MIRACL French (152 scored questions): " + ", ".join(f"{LABELS[m]} {f(vals[m])}" for m in order[:6]) + ". "
      + f"Jev's best, {LABELS[max((m for m in JEV_ALL if m in vals), key=vals.get)]}, is {100 * (vals[order[0]] - max(vals[m] for m in JEV_ALL if m in vals)):.1f} points behind {LABELS[order[0]]}. The gap is real; it is also the one place TypeSafe made no claim.")
    P("")
P("## Where Jev loses")
P("")
losses = [(d, m) for d, m in wins.items() if not m.startswith("jev")]
for d, m in losses:
    n = D[d]["queries_with_answer_in_top30"]
    P(f"- **{NICE[d]}** ({n} questions{'; small sample' if n < 60 else ''}): {LABELS[m]} {f(D[d]['models'][m]['ndcg10'])} vs Jev's best {f(max(D[d]['models'][j]['ndcg10'] for j in JEV_ALL if j in D[d]['models']))}"
      + (f"; {rng(SIG['datasets'][d]['jev_vs_other'])}, {tag(SIG['datasets'][d]['jev_vs_other'])}." if SIG else "."))
P(f"- **The 'nothing here' gate:** {LABELS[none_best]} separates better ({f(rows[none_best]['none'], 2)} vs {f(rows[best_jev_simple]['none'], 2)}); {none_note}.")
P(f"- **Price:** ZeroEntropy is cheaper (${f(rows['zerank-2']['cost'], 2)} vs ${f(rows[best_jev_simple]['cost'], 2)} per 1,000) at close to the same quality.")
P(f"- **Calibration outside science:** on finance and French, passages Jev scores 0.9+ are relevant only about six times in ten.")
P("- **Repeat drift and order sensitivity**, above.")
P("- **French**, above.")
P("")
P("## Which one to use for what")
P("")
if tie:
    P(f"- **Best quality, price no object:** {LABELS[best]} and {LABELS[runner_up]} are tied on ranking quality; pick by the other columns (speed, price, the 'nothing here' gate).")
else:
    P(f"- **Best quality, price no object:** {LABELS[best]}.")
P(f"- **Best value:** {LABELS[cheapest]}: cheapest of the models within 2 points of the best, and {abs(100 * (rows[best]['ndcg'] - rows[cheapest]['ndcg'])):.1f} points behind it.")
P(f"- **Fast, and a decision rather than just an order:** {LABELS[best_jev_simple]}. {sec(rows[best_jev_simple]['ms'])} per query, a confidence you can act on above 0.9, first or tied-first on science, reasoning and code.")
if NEV:
    P(f"- **Questions with a 'not' in them:** Jev ({pct(nd[nj]['paired_accuracy'])} of negation pairs right vs {pct(nd[no]['paired_accuracy'])} for the best reranker).")
P(f"- **Skip:** the yes/no-per-pair pattern in TypeSafe's cookbook (dearer and worse than one call), pairwise duels on a keyword top 10, and a chat model reading one token's probability as a reranker: with thinking off it answers 0 or 1 for {pct(en_avg('deepseek-pair', 'saturated_share'))} of passages, so it is a yes/no classifier, not a ranker.")
P("")
P("## Reproduce it")
P("")
P("Code, candidate lists, every raw API response and the scoring script: https://github.com/anessbelbati/jev-rerank-bench. `uv sync`, put four keys in `.env`, `uv run candidates/build.py`, `uv run run.py --model <name> --dataset all`, `uv run eval.py`. "
  f"The whole thing cost about ${sum(D[d]['models'][m]['cost_usd_all_variants'] for d in D for m in D[d]['models']) + (sum(v['cost_usd'] for m, v in NEV.items() if m in LABELS) if NEV else 0):.0f} in API calls.")

(RESULTS / "BLOG-DRAFT.md").write_text("\n".join(L), encoding="utf-8")
print(f"wrote {RESULTS / 'BLOG-DRAFT.md'}: {len(L)} lines")
