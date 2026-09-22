"""Run small open "decision" models as rerankers on a rented GPU, one passage per question (the jev-noul-pair shape).

- laya-noul-pair       : convaiinnovations/laya (ModernBERT-large, 421M), one yes/no per (query, passage), the same question and
                         true/false wording Jev got; score = P(true). Its window is 512 tokens, so a long passage is cut
                         by the library itself; the number of cut passages is saved on every row.
- laya-score-pair      : same model, the four-level rubric Jev's Score mode got; score = expected level / 3.
- laya-multi-noul-pair : the multilingual checkpoint (mmBERT-base, 1024-token window), yes/no.
- gliner25-{small,base,multi}-pair : fastino/gliner2.5-*-v1, two-label classification of "Query: ...\n\nPassage: ..." with
                         the same relevant / not-relevant wording as label descriptions; score = P(relevant).

Laya's library answers one state per call; here the 30 pairs of a query go through the model as one batch using the
library's own build_sequence / collate_items / temperatures, and the first query is checked against agent.predict.

Writes rows in the exact cache format run.py uses, so eval.py / significance.py / nevir_eval.py need no changes.
Cost = GPU seconds x the pod's hourly price (passed in). Latency = wall clock for the 30 pairs of one query on the GPU.

Usage (on the pod):
    python small_models_runner.py --root /workspace/jev --rate 0.74 --gpu "RTX 4090" --models laya-noul-pair ... --datasets scifact ...
"""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
import torch

QUESTION = "Does the passage contain the information needed to answer or verify the query?"
TRUE = "The passage states or directly implies the answer to the query, or the evidence that verifies it."
FALSE = "The passage is only on a related topic; it does not supply what the query asks for."
RUBRIC = ["The passage is off-topic for the query.",
          "The passage is on a related topic but does not supply what the query asks for.",
          "The passage partly supplies the information needed to answer or verify the query.",
          "The passage fully supplies the information needed to answer or verify the query."]
SCORE_QUESTION = "How well does the passage supply the information needed to answer or verify the query?"

LAYA = {"laya-noul-pair": ("convaiinnovations/laya", None, "noul"),
        "laya-score-pair": ("convaiinnovations/laya", None, "score"),
        "laya-multi-noul-pair": ("convaiinnovations/laya-multilingual", "multilingual", "noul")}
GLINER = {"gliner25-small-pair": "fastino/gliner2.5-small-v1",
          "gliner25-base-pair": "fastino/gliner2.5-base-v1",
          "gliner25-multi-pair": "fastino/gliner2.5-multi-v1"}


def read_jsonl(p: Path):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


class LayaScorer:
    def __init__(self, repo: str, subfolder: str | None, qtype: str):
        import laya
        try:
            self.agent = laya.load(repo)
            self.source = repo
        except Exception:
            self.agent = laya.load("convaiinnovations/laya", subfolder=subfolder)
            self.source = f"convaiinnovations/laya [{subfolder}]"
        self.q = ({"type": "noul", "instructions": QUESTION, "criteria": {"true": TRUE, "false": FALSE}} if qtype == "noul"
                  else {"type": "score", "instructions": SCORE_QUESTION, "criteria": RUBRIC})
        # torch 2.4's fused attention returns NaN at padded positions that sit outside every real token's local window,
        # and the next layer spreads them (0 weight x NaN value = NaN). Real tokens never read padded ones, so zeroing
        # the NaNs after each layer leaves every real token's value unchanged.
        def _zero_nan(_m, _inp, out):
            if isinstance(out, tuple):
                return (torch.nan_to_num(out[0], nan=0.0),) + tuple(out[1:])
            return torch.nan_to_num(out, nan=0.0)
        for layer in self.agent.model.encoder.layers:
            layer.register_forward_hook(_zero_nan)
        self.qtype = qtype
        self.checked = False

    def _value(self, answer: dict) -> float:
        return answer["noul"] if self.qtype == "noul" else answer["score"] / (len(RUBRIC) - 1)

    @torch.no_grad()
    def score(self, query: str, docs: list[str]):
        from laya.common import QTYPES, build_sequence, collate_items, temp_bucket
        a = self.agent
        q = a._to_internal(self.q)
        max_len, head = a.cfg.get("max_len", 512), a.cfg.get("head_max_len", 192)
        items, cut = [], 0
        for d in docs:
            state = {"query": query, "passage": d}
            seq, markers = build_sequence(a.tok, state, q, max_len, head)
            cut += int(len(build_sequence(a.tok, state, q, 10 ** 6, head)[0]) > max_len)
            items.append({"ids": seq, "markers": markers, "qtype": QTYPES[q["t"]]})
        b = collate_items([items], a.tok.pad_token_id)
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        with torch.autocast(device_type="cuda", dtype=a.dtype):
            logits, _ = a.model(b["input_ids"].to(a.device), b["attention_mask"].to(a.device), b["marker_pos"].to(a.device),
                                b["marker_mask"].to(a.device), b["qtype"].to(a.device))
        logits = logits.float().cpu().numpy()
        torch.cuda.synchronize()
        ms = (time.perf_counter() - t0) * 1000
        scores = []
        for r in range(len(docs)):
            k = len(items[r]["markers"])
            qt = QTYPES[q["t"]]
            z = logits[r, :k] / max(1e-3, float(a.temperature_by_options.get(temp_bucket(qt, k), a.temperature[qt])))
            p = np.exp(z - z.max())
            p = p / p.sum()
            scores.append(float(p[1]) if self.qtype == "noul" else float((np.arange(k) * p).sum()) / (len(RUBRIC) - 1))
        raw = {"mode": "pair_batched", "source": self.source, "pairs": len(docs), "passages_cut_by_window": cut,
               "tokens": int(b["attention_mask"].sum()), "window": max_len}
        if not self.checked:
            ref = [self._value(a.predict({"query": query, "passage": d}, {"x": self.q})["answers"]["x"]) for d in docs[:8]]
            raw["check_vs_predict_max_abs_diff"] = round(max(abs(x - y) for x, y in zip(ref, scores[:8])), 5)
            print("batched vs library predict, first 8 passages, max abs diff:", raw["check_vs_predict_max_abs_diff"], flush=True)
            self.checked = True
        return scores, ms, raw


class GlinerScorer:
    def __init__(self, repo: str):
        from gliner2 import AutoExtractor
        from huggingface_hub import snapshot_download
        d = snapshot_download(repo, local_dir="/workspace/models/" + repo.split("/")[1])
        cfg = os.path.join(d, "tokenizer_config.json")
        c = json.load(open(cfg))
        if isinstance(c.get("extra_special_tokens"), list):     # saved by a newer transformers; 4.57 wants a mapping
            c["extra_special_tokens"] = {"extra_%d" % i: t for i, t in enumerate(c["extra_special_tokens"])}
            json.dump(c, open(cfg, "w"), indent=2)
        self.model = AutoExtractor.from_pretrained(d)
        self.model.to("cuda")
        self.source = repo
        self.tasks = {"relevance": {"labels": {"relevant": TRUE, "not_relevant": FALSE}}}

    @torch.no_grad()
    def score(self, query: str, docs: list[str]):
        texts = [f"Query: {query}\n\nPassage: {d}" for d in docs]
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        out, used = None, None
        for bs in (len(texts), 6, 1):       # code-heavy passages tokenize long; each text is judged alone, so a smaller batch gives the same scores
            try:
                out = self.model.batch_classify_text(texts, self.tasks, batch_size=bs, include_confidence=True)
                used = bs
                break
            except torch.cuda.OutOfMemoryError:
                torch.cuda.empty_cache()
        if out is None:
            raise RuntimeError("out of GPU memory even one passage at a time")
        torch.cuda.synchronize()
        ms = (time.perf_counter() - t0) * 1000
        scores = []
        for o in out:
            r = o["relevance"]
            scores.append(float(r["confidence"]) if r["label"] == "relevant" else 1.0 - float(r["confidence"]))
        return scores, ms, {"mode": "pair_batched", "source": self.source, "pairs": len(docs), "batch_size_used": used}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--rate", type=float, required=True, help="pod price, USD per hour")
    ap.add_argument("--gpu", required=True)
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--datasets", nargs="+", required=True)
    ap.add_argument("--max-chars", type=int, default=2000)
    ap.add_argument("--variants", nargs="+", default=["present", "absent"])
    ap.add_argument("--limit", type=int, default=0, help="first N rows per dataset (smoke test)")
    ap.add_argument("--shard", default="0/1", help="k/n: this pod takes every n-th row starting at k")
    ap.add_argument("--only", default=None, help="JSON {\"model/ds.variant\": [qid, ...]}: redo just these lists; the shard then splits that list")
    args = ap.parse_args()
    shard_k, shard_n = (int(x) for x in args.shard.split("/"))
    only = json.load(open(args.only, encoding="utf-8")) if args.only else None
    gpu = f"{torch.cuda.get_device_name(0)}, {args.gpu}"
    root = Path(args.root)
    for key in args.models:
        scorer = LayaScorer(*LAYA[key]) if key in LAYA else GlinerScorer(GLINER[key])
        print("loaded", key, "from", scorer.source, flush=True)
        for ds in args.datasets:
            docs = {r["did"]: r["text"] for r in read_jsonl(root / "candidates" / f"{ds}.docs.jsonl")}
            rows = read_jsonl(root / "candidates" / f"{ds}.jsonl")
            if only is None:
                rows = rows[shard_k::shard_n]
            if args.limit:
                rows = rows[:args.limit]
            for variant in args.variants:
                out = root / "cache" / key / f"{ds}.{variant}.jsonl"
                out.parent.mkdir(parents=True, exist_ok=True)
                done = {r["qid"] for r in map(json.loads, open(out, encoding="utf-8")) if r["ok"]} if out.exists() else set()
                todo = [r for r in rows if r.get(variant) and r["qid"] not in done]
                if only is not None:
                    want = set(only.get(f"{key}/{ds}.{variant}", ()))
                    todo = [r for r in todo if r["qid"] in want][shard_k::shard_n]
                if not todo:
                    continue
                t_start = time.time()
                with open(out, "a", encoding="utf-8") as f:
                    for n, r in enumerate(todo, 1):
                        cands = r[variant]
                        texts = [docs[c["did"]][:args.max_chars] for c in cands]
                        try:
                            scores, ms, raw = scorer.score(r["query"], texts)
                            ok, err = True, None
                        except Exception as e:                      # keep going; the row is redone on the next run
                            scores, ms, raw, ok, err = [None] * len(cands), 0.0, None, False, f"{type(e).__name__}: {e}"[:300]
                            torch.cuda.empty_cache()
                        cost = ms / 3.6e6 * args.rate
                        row = {"qid": r["qid"], "variant": variant, "model": key, "dids": [c["did"] for c in cands], "scores": scores,
                               "extra": {"gpu": gpu, "usd_per_hour": args.rate, "shard": args.shard}, "ok": ok, "cost_usd": cost, "query_ms": ms,
                               "calls": [{"latency_ms": ms, "status": 200 if ok else 0, "usage": {"gpu_ms": ms}, "cost_usd": cost, "raw": raw, "error": err}],
                               "workers": 1, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")
                        if n % 200 == 0 or n == len(todo):
                            print(f"{key} {ds} {variant}: {n}/{len(todo)}  {n / (time.time() - t_start):.2f} q/s  last {ms:.0f} ms", flush=True)
        del scorer
        torch.cuda.empty_cache()
    print("done", flush=True)


if __name__ == "__main__":
    main()
