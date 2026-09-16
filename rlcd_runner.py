"""Run the "Qwen-2.5-1B-RLCD" recipe (Qwen2.5-1.5B-Instruct + parallel constrained decoding of JSON keys) as a reranker.

This is the open-source answer to Jev that appeared on X the day after the launch: no training, one prefill of the
prompt, then every JSON key is scored in one batched pass by a softmax over the allowed answers. We run the
transformers port (huggingface.co/shreyansh26/Qwen-2.5-1B-RLCD, Apache 2.0; the original is Apple-MLX only) with its
own `run_parallel_generation`, on a rented GPU, in two modes that mirror the Jev one-call modes:

- qwen-rlcd-batch : 30 boolean keys, one per passage, same wording as Jev's yes/no; score = P(true)
- qwen-rlcd-rubric: 30 enum keys with the same four-level rubric as Jev's Score mode; score = expected level / 3

Writes rows in the exact cache format run.py uses, so eval.py / significance.py / nevir_eval.py need no changes.
Cost = GPU seconds × the pod's hourly price (passed in). Latency = wall clock of the model call on the GPU.

Usage (on the pod, with the RLCD repo's `core/` package on sys.path):
    python rlcd_runner.py --root /workspace/jev --rate 0.34 --gpu "RTX 4090" --datasets scifact fiqa ...
"""
from __future__ import annotations

import argparse
import gc
import json
import sys
import time
from pathlib import Path

import torch

RUBRIC = ["off-topic", "related", "partly", "fully"]
RUBRIC_DESC = ("off-topic = the passage is off-topic for the query; related = on a related topic but does not supply what "
               "the query asks for; partly = partly supplies the information needed to answer or verify the query; "
               "fully = fully supplies it")
QUESTION = "Does the passage contain the information needed to answer or verify the query?"


def read_jsonl(p: Path):
    with open(p, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def context_for(query: str, docs: list[str]) -> str:
    parts = [f"Query: {query}", "", "Passages:"]
    for i, d in enumerate(docs):
        parts.append(f"p{i + 1:02d}: {d}")
    return "\n".join(parts)


def schema_for(mode: str, n: int):
    from core.schema import StructuredSchema
    if mode == "batch":
        spec = {f"p{i + 1:02d}": {"type": "boolean", "description": f"{QUESTION} (passage p{i + 1:02d})"} for i in range(n)}
    else:
        spec = {f"p{i + 1:02d}": {"type": "enum", "choices": RUBRIC, "description": f"How well passage p{i + 1:02d} answers the query: {RUBRIC_DESC}"} for i in range(n)}
    return StructuredSchema(spec)


def run_parallel_chunked(context: str, schema, chunk: int = 6, temperature: float = 1.0) -> dict:
    """Same computation as core.engine.run_parallel_generation (same prompt, one prefill, each field's suffix scored
    against the shared cache, softmax over the allowed first tokens), but the fields are evaluated `chunk` at a time so
    the KV cache is repeated 6x instead of 30x. Used only when the one-shot call runs out of GPU memory; the scores are
    identical because every field is scored independently given the same prefix."""
    import copy
    from core.engine import get_engine, _synchronize, _candidate_scores
    model, tokenizer = get_engine()
    with torch.inference_mode():
        meta = schema.compile_parallel_metadata(tokenizer)
        prompt = (f"<|im_start|>system\nClassify JSON attributes:\n{schema.to_parallel_schema_str()}"
                  f"<|im_end|>\n<|im_start|>user\n{context}<|im_end|>\n<|im_start|>assistant\n{{\n")
        inputs = tokenizer(prompt, add_special_tokens=False, return_tensors="pt").to(model.device)
        t0 = time.perf_counter()
        out = model(**inputs, use_cache=True, logits_to_keep=1)
        cache = out.past_key_values
        prefix_length = cache.get_seq_length()
        del out
        items = meta["field_items"]
        telemetry, passes = {}, 1
        for start in range(0, len(items), chunk):
            idx = list(range(start, min(len(items), start + chunk)))
            branch = copy.deepcopy(cache)
            branch.batch_repeat_interleave(len(idx))
            suffixes = meta["suffixes_batch"][idx].to(model.device)
            smask = meta["suffix_attention_mask"][idx].to(model.device)
            attention = torch.cat([inputs["attention_mask"].repeat(len(idx), 1), smask], dim=1)
            o = model(input_ids=suffixes, attention_mask=attention, past_key_values=branch, use_cache=True)
            passes += 1
            for j, i in enumerate(idx):
                name, field = items[i]
                length = meta["suffix_lengths"][i]
                logits = o.logits[j, length - 1]
                cands = meta["candidate_sequences"][i]
                if meta["has_collisions"][i]:
                    b2 = copy.deepcopy(branch)
                    b2.batch_select_indices(torch.tensor([j], device=model.device))
                    padding = b2.get_seq_length() - prefix_length - length
                    if padding:
                        b2.crop(-padding)
                    scores, extra = _candidate_scores(model, b2, logits, cands, tokenizer.pad_token_id)
                    passes += extra
                    del b2
                else:
                    scores = logits[[t[0] for t in cands]].float()
                probs = torch.softmax(scores / max(temperature, 1e-4), dim=-1).tolist()
                telemetry[name] = {"top_choices": [{"choice": c, "probability": round(pp, 4)} for c, pp in zip(field.choices, probs)]}
            del o, branch
            torch.cuda.empty_cache()
        _synchronize(model)
    return {"mode": "parallel_constrained_chunked", "elapsed_ms": round((time.perf_counter() - t0) * 1000, 2), "prefill_ms": None,
            "suffix_eval_ms": None, "sequential_forward_passes": passes, "field_telemetry": telemetry}


def score_row(mode: str, query: str, docs: list[str]):
    from core.engine import run_parallel_generation
    schema = schema_for(mode, len(docs))
    t0 = time.perf_counter()
    try:
        res = run_parallel_generation(context_for(query, docs), schema, temperature=1.0)
    except torch.cuda.OutOfMemoryError:
        res = None          # the fallback must run outside this block: the traceback keeps the failed 30x cache alive
    if res is None:
        gc.collect()
        torch.cuda.empty_cache()
        res = run_parallel_chunked(context_for(query, docs), schema)
    ms = (time.perf_counter() - t0) * 1000
    scores = []
    for i in range(len(docs)):
        tel = res["field_telemetry"][f"p{i + 1:02d}"]
        probs = {c["choice"]: c["probability"] for c in tel["top_choices"]}
        if mode == "batch":
            scores.append(probs.get("true", 0.0))
        else:
            scores.append(sum(probs.get(c, 0.0) * k for k, c in enumerate(RUBRIC)) / (len(RUBRIC) - 1))
    raw = {"mode": res["mode"], "elapsed_ms": res["elapsed_ms"], "prefill_ms": res["prefill_ms"], "suffix_eval_ms": res["suffix_eval_ms"],
           "sequential_forward_passes": res["sequential_forward_passes"], "field_telemetry": res["field_telemetry"]}
    return scores, ms, raw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--rate", type=float, required=True, help="pod price, USD per hour")
    ap.add_argument("--gpu", required=True)
    ap.add_argument("--datasets", nargs="+", required=True)
    ap.add_argument("--modes", nargs="+", default=["batch", "rubric"])
    ap.add_argument("--max-chars", type=int, default=2000)
    args = ap.parse_args()
    root = Path(args.root)
    for mode in args.modes:
        key = f"qwen-rlcd-{mode}"
        for ds in args.datasets:
            docs = {r["did"]: r["text"] for r in read_jsonl(root / "candidates" / f"{ds}.docs.jsonl")}
            rows = read_jsonl(root / "candidates" / f"{ds}.jsonl")
            for variant in ("present", "absent"):
                out = root / "cache" / key / f"{ds}.{variant}.jsonl"
                out.parent.mkdir(parents=True, exist_ok=True)
                done = {r["qid"] for r in map(json.loads, open(out, encoding="utf-8")) if r["ok"]} if out.exists() else set()
                todo = [r for r in rows if r[variant] and r["qid"] not in done]
                if not todo:
                    continue
                t_start = time.time()
                with open(out, "a", encoding="utf-8") as f:
                    for n, r in enumerate(todo, 1):
                        cands = r[variant]
                        texts = [docs[c["did"]][:args.max_chars] for c in cands]
                        try:
                            scores, ms, raw = score_row(mode, r["query"], texts)
                            ok, err = True, None
                        except Exception as e:                      # keep going; the row is redone on the next run
                            scores, ms, raw, ok, err = [None] * len(cands), 0.0, None, False, f"{type(e).__name__}: {e}"[:300]
                            torch.cuda.empty_cache()
                        cost = ms / 3.6e6 * args.rate
                        row = {"qid": r["qid"], "variant": variant, "model": key, "dids": [c["did"] for c in cands], "scores": scores,
                               "extra": {"gpu": args.gpu, "usd_per_hour": args.rate}, "ok": ok, "cost_usd": cost, "query_ms": ms,
                               "calls": [{"latency_ms": ms, "status": 200 if ok else 0, "usage": {"gpu_ms": ms}, "cost_usd": cost, "raw": raw, "error": err}],
                               "workers": 1, "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
                        f.write(json.dumps(row, ensure_ascii=False) + "\n")
                        if n % 50 == 0 or n == len(todo):
                            rate = n / (time.time() - t_start)
                            print(f"{key} {ds} {variant}: {n}/{len(todo)}  {rate:.2f} q/s  last {ms:.0f} ms", flush=True)
    print("done")


if __name__ == "__main__":
    main()
