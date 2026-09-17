"""Deterministic, offline export of the recorded reranker evidence for a static viewer.

Run with .venv/Scripts/python.exe -B -X utf8 scripts/export_evidence.py.
The exporter never invokes a provider or downloads a corpus. It deliberately excludes
credentials, HTTP headers, request IDs, arbitrary provider metadata and full corpora.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import inspect
import json
import math
import statistics
import subprocess
import sys
import types
import zipfile
import zlib
from collections import Counter, defaultdict
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common import BRIGHT, CACHE, CANDIDATES, DATASETS, ENGLISH, MAX_CHARS, PRICES, read_jsonl
from eval import LABELS, MODELS, PROB_MODELS, auroc, calibration, mrr, ndcg, order, order_worst, percentile, recall
from rerankers import REGISTRY, RELEVANCE_FALSE, RELEVANCE_QUESTION, RELEVANCE_TRUE

SCHEMA = "1.1"
REPO = "https://github.com/anessbelbati/jev-rerank-bench"
PUBLIC = ROOT / "exports" / "evidence"
METRICS = ("ndcg10", "ndcg10_ties_against", "recall5", "top1", "mrr10", "tied_top_share")
LABEL_DATASETS = {"scifact": "SciFact", "fiqa": "FiQA", "nq": "Natural Questions", "nfcorpus": "NFCorpus", "trec-covid": "TREC-COVID", "csn-python": "CodeSearchNet Python", "miracl-fr": "MIRACL French", "nevir": "NevIR"}
DESCRIPTIONS = {
    "bm25": "Recorded BM25 scores; equal scores preserve the original candidate order.",
    "jev-noul-pair": "One relevance yes/no request per passage (30 requests for a normal retrieval query).",
    "jev-noul-batch": "All 30 relevance yes/no judgments in one request.",
    "jev-choice": "One request with a passage Choice plus none and a separate any-relevant judgment.",
    "jev-choice-reversed": "The Choice configuration with input passages reversed; exported scores are aligned to original candidate order.",
    "jev-score-batch": "One request with a four-level relevance rubric for every passage; score is expected rubric level divided by three.",
    "jev-duel": "45 pairwise Choices over the first 10 BM25 passages in one request; other passages remain below these ten.",
    "jev-tournament": "Six five-passage Choices, then a final Choice among group winners; winners always rank above other passages.",
    "jev-cascade": "Batched yes/no pruning to eight passages followed by eight individual requests; kept passages always rank above pruned ones.",
    "cohere-pro": "Cohere Rerank 4 Pro via OpenRouter; one request for the candidate set.",
    "cohere-fast": "Cohere Rerank 4 Fast via OpenRouter; one request for the candidate set.",
    "zerank-2": "ZeroEntropy zerank-2; one request for the candidate set.",
    "deepseek-pair": "DeepSeek V4.1 Flash via OpenRouter pinned to DeepSeek with fallbacks and reasoning disabled; normalized first-token P(yes) per passage.",
    "deepseek-json": "Same DeepSeek routing; one JSON request with integer 0–100 scores for all passages. The original adapter substitutes zero for missing IDs; extra.missing_ids exposes that behavior.",
    "qwen-rlcd-batch": "Self-hosted Qwen2.5-1.5B-Instruct with the RLCD Transformers recipe: 30 boolean keys share one prompt; score is normalized P(true). Cost is an estimate from recorded GPU-call time, excluding setup and idle time; latency is measured on the GPU host, without an API network round trip.",
    "qwen-rlcd-rubric": "Self-hosted Qwen RLCD with 30 four-level rubric keys; score is expected level divided by three. Cost estimates cover recorded GPU-call time only; latency is measured on the GPU host. Memory fallback modes are retained in the evidence.",
    "qwen-rlcd-pair": "Self-hosted Qwen RLCD with one passage and one boolean key per prompt; 30 sequential prompts per retrieval query, scored by normalized P(true). Cost estimates cover recorded GPU-call time only; latency includes every sequential prompt but no API network round trip.",
    "qwen-rlcd-batch-reversed": "Order-sensitivity diagnostic for Qwen's 30-key boolean mode: passages are reversed at input, then scores are mapped back to original candidate order. Recorded only for present queries in the original eight datasets. GPU-time cost estimate; not an independent model or a separate trained configuration.",
}
QWEN_PREFIX = "qwen-rlcd-"
QWEN_COST_NOTE = "Estimate: recorded query wall-clock milliseconds / 3,600,000 × the row's GPU hourly rate. Excludes pod setup, model loading, idle time and other billed time outside the query timer; not an API invoice or total hosting cost."
QWEN_LATENCY_NOTE = "Wall-clock model-call time measured on the GPU host; pair mode includes all sequential prompts. No client-to-provider network round trip. Not directly comparable with hosted API timings or production throughput."
MIT_PERMISSION = """Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the \"Software\"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE."""


def license_notices():
    return {"schema_version": SCHEMA, "verified_date": "2026-09-16", "notice": "Dataset cards identify the collection licenses. These notices do not replace underlying document authorship or licenses. Only candidate excerpts used in the experiment are included, with document IDs and dataset source links.",
            "mit": [{"dataset": dataset, "source_url": url, "notice": f"MIT License\n\nCopyright (c) {copyright}\n\n{MIT_PERMISSION}"} for dataset, url, copyright in [("CodeSearchNet", "https://github.com/github/CodeSearchNet/blob/master/LICENSE", "2019 GitHub"), ("NevIR", "https://github.com/orionw/NevIR/blob/main/LICENSE", "2023 Orion Weller")]],
            "creative_commons": [{"license": "CC BY 4.0", "url": "https://creativecommons.org/licenses/by/4.0/"}, {"license": "CC BY-SA 4.0", "url": "https://creativecommons.org/licenses/by-sa/4.0/"}],
            "excerpt_changes": "Title and text joined where available; truncated to the first 2,000 characters. Source texts are rendered as plain text. Original article URLs were not retained in the candidate records."}


def family(model):
    return "Qwen RLCD" if model.startswith(QWEN_PREFIX) else "Jev" if model.startswith("jev-") else "DeepSeek" if model.startswith("deepseek-") else "Cohere" if model.startswith("cohere-") else "ZeroEntropy" if model == "zerank-2" else "BM25"


def model_metadata(model):
    result = {"id": model, "label": LABELS[model], "family": family(model), "description": DESCRIPTIONS[model], "prompt_id": model,
              "experiment_role": "order_sensitivity_diagnostic" if model.endswith("-reversed") else "reranker_configuration"}
    if model.startswith(QWEN_PREFIX):
        result.update(cost_basis="gpu_time_estimate", cost_note=QWEN_COST_NOTE, latency_basis="gpu_host_wall_clock", latency_note=QWEN_LATENCY_NOTE,
                      base_model="Qwen/Qwen2.5-1.5B-Instruct", implementation="shreyansh26/Qwen-2.5-1B-RLCD Transformers port", source_url=f"{REPO}/blob/main/rlcd_runner.py")
    return result


def source(dataset):
    if dataset.startswith("bright-"):
        repo, license_id = "mteb/BrightRetrieval", "cc-by-4.0"
        creator = "BRIGHT authors (Su et al., 2024), packaged by MTEB"
    elif dataset == "csn-python":
        repo, license_id, creator = "mteb/CodeSearchNetRetrieval", "mit", "CodeSearchNet authors, packaged by MTEB"
    elif dataset == "miracl-fr":
        repo, license_id, creator = "mteb/MIRACLReranking", "cc-by-sa-4.0", "MIRACL authors, packaged by MTEB"
    elif dataset == "nevir":
        repo, license_id, creator = "orionweller/NevIR", "mit", "Orion Weller and NevIR contributors"
    else:
        repo, license_id, creator = f"BeIR/{dataset}", "cc-by-sa-4.0", "Original dataset authors, packaged by BEIR"
    url = f"https://huggingface.co/datasets/{repo}"
    return {"url": url, "dataset_card_url": url, "license": license_id,
            "license_url": "https://opensource.org/license/mit" if license_id == "mit" else f"https://creativecommons.org/licenses/{license_id.removeprefix('cc-') .removesuffix('-4.0')}/4.0/",
            "attribution": creator, "verified_date": "2026-09-16",
            "content_note": "Candidate excerpts only, cut to the first 2,000 characters exactly as supplied to models. Dataset-card license is reported; underlying authors retain their rights. Original article URLs were not preserved in the saved candidates; source links identify the dataset and document IDs identify its rows.",
            "modifications": "Title and text joined by a newline where available; excerpts truncated to 2,000 characters. No full corpus included."}


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def clean(value):
    """JSON-safe values only; non-finite measurements are unavailable, never zero."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [clean(v) for v in value]
    return value


def encoded(obj):
    return (json.dumps(clean(obj), ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = encoded(obj)
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)
    return len(data)


def mean(xs):
    xs = list(xs)
    return statistics.mean(xs) if xs else None


def detail_url(dataset, qid):
    return f"data/{dataset}/queries/{hashlib.sha256(str(qid).encode()).hexdigest()[:20]}.json"


def latest(model, dataset, variant):
    rows = read_jsonl(CACHE / model / f"{dataset}.{variant}.jsonl")
    values = {str(r["qid"]): r for r in rows}
    return values, len(rows) - len(values)


USAGE_FIELDS = {"input_tokens", "output_tokens", "prompt_tokens", "completion_tokens", "total_tokens", "total_bytes", "search_units", "cost", "inference_latency_s", "latency_mode", "served_model", "provider", "gpu_ms"}
EXTRA_FIELDS = {"none_prob", "any_prob", "choice", "confidence", "reversed", "wins", "duels", "winners", "kept", "p_yes_raw", "provider", "missing_ids", "gpu", "usd_per_hour"}
ANSWER_FIELDS = {"type", "noul", "choice", "confidence", "score", "probabilities", "legend"}


def sanitized_rlcd_telemetry(value):
    result = {k: v for k, v in value.items() if k in {"value", "type", "confidence", "cardinality", "prefill_ms", "suffix_eval_ms"}}
    if isinstance(value.get("top_choices"), list):
        result["top_choices"] = [{k: v for k, v in c.items() if k in {"choice", "probability"}} for c in value["top_choices"] if isinstance(c, dict)]
    return result


def sanitized_call(call):
    raw = call.get("raw")
    result = {"status": call.get("status"), "latency_ms": call.get("latency_ms"), "cost_usd": call.get("cost_usd"),
              "usage": {k: v for k, v in (call.get("usage") or {}).items() if k in USAGE_FIELDS}}
    error = call.get("error")
    result["error"] = None if not error else f"HTTP {call.get('status')}" if str(error).startswith("HTTP ") else "No log probabilities in response" if error == "no logprobs in response" else "Invalid JSON response" if str(error).startswith("bad JSON:") else "Recorded call error (provider details omitted)"
    if not isinstance(raw, dict):
        return result
    output = {}
    if isinstance(raw.get("model"), str):
        output["model"] = raw["model"]
    if isinstance(raw.get("answers"), dict):
        output["answers"] = {str(k): {field: value for field, value in answer.items() if field in ANSWER_FIELDS} for k, answer in raw["answers"].items() if isinstance(answer, dict)}
    if isinstance(raw.get("results"), list):
        output["results"] = [{k: v for k, v in row.items() if k in {"index", "relevance_score"}} for row in raw["results"] if isinstance(row, dict)]
    if isinstance(raw.get("choices"), list):
        output["choices"] = []
        for ch in raw["choices"]:
            entry = {"content": (ch.get("message") or {}).get("content"), "finish_reason": ch.get("finish_reason")}
            logprobs = (ch.get("logprobs") or {}).get("content")
            if logprobs:
                entry["first_token_logprobs"] = {"token": logprobs[0].get("token"), "logprob": logprobs[0].get("logprob"), "top_logprobs": [{"token": t.get("token"), "logprob": t.get("logprob")} for t in logprobs[0].get("top_logprobs", [])]}
            output["choices"].append(entry)
    # RLCD records engine telemetry instead of an HTTP response. Preserve the actual
    # allowed-label probabilities and memory fallback mode, not arbitrary pod metadata.
    for key in ("mode", "elapsed_ms", "prefill_ms", "suffix_eval_ms", "sequential_forward_passes", "prompts", "passage_order"):
        if key in raw:
            output[key] = raw[key]
    if isinstance(raw.get("field_telemetry"), dict):
        output["field_telemetry"] = {str(k): sanitized_rlcd_telemetry(v) for k, v in raw["field_telemetry"].items() if isinstance(v, dict)}
    if isinstance(raw.get("per_passage"), list):
        output["per_passage"] = [sanitized_rlcd_telemetry(v) for v in raw["per_passage"] if isinstance(v, dict)]
    result["output"] = output
    return result


def row_status(row, candidates):
    if row is None:
        return "missing"
    if not row.get("ok"):
        return "failed"
    if row.get("dids") != [c["did"] for c in candidates]:
        return "invalid_candidate_alignment"
    if len(row.get("scores", [])) != len(candidates) or not all(finite(x) for x in row["scores"]):
        return "invalid_scores"
    return "ok"


def metrics(row, relevant, eligible, nevir=False):
    rank = order(row)
    result = {k: None for k in METRICS if k != "tied_top_share"}
    result.update(tied_top=row["scores"].count(max(row["scores"])) > 1, top_did=rank[0])
    if nevir:
        scores = dict(zip(row["dids"], row["scores"]))
        result["question_correct"] = scores[next(iter(relevant))] > max(scores[d] for d in scores if d not in relevant)
    elif eligible:
        result.update(ndcg10=ndcg(rank, relevant), ndcg10_ties_against=ndcg(order_worst(row), relevant),
                      recall5=recall(rank, relevant), top1=float(rank[0] in relevant), mrr10=mrr(rank, relevant))
    return result


def export_row(row, candidates, relevant, eligible, nevir=False):
    status = row_status(row, candidates)
    result = {"status": status, "scores": None, "ranking": None, "metrics": None, "cost_usd": None, "query_ms": None, "calls": [], "extra": {}}
    if row is None:
        return result
    result.update(scores=row.get("scores"), cost_usd=row.get("cost_usd"), query_ms=row.get("query_ms"), workers=row.get("workers"), timestamp=row.get("ts"),
                  calls=[sanitized_call(c) for c in row.get("calls", [])], extra={k: v for k, v in row.get("extra", {}).items() if k in EXTRA_FIELDS})
    if status == "ok":
        result["ranking"] = order(row)
        result["metrics"] = metrics(row, relevant, eligible, nevir)
    return result


def summarize_model(model, cands, runs, query_models, nevir=False):
    present, absent = runs["present"], runs["absent"]
    eligible = [r for r in cands if r["n_rel_top30"] > 0]
    ok = [r for r in eligible if query_models[r["qid"]][model]["status"] == "ok"]
    existing = [present[r["qid"]] for r in cands if r["qid"] in present]
    statuses = Counter(query_models[r["qid"]][model]["status"] for r in eligible)
    cost_values = [r["cost_usd"] for r in existing if finite(r.get("cost_usd"))]
    result = {"n": len(ok), "queries_total": len(cands), "queries_eligible": len(eligible), "present_recorded": len(existing),
              "missing": statuses["missing"], "failed": sum(v for k, v in statuses.items() if k not in {"ok", "missing"}),
              "status_counts": dict(statuses), "coverage_complete": len(ok) == len(eligible),
              "cost_queries": len(cost_values), "cost_usd_present": sum(cost_values) if cost_values else None,
              "cost_per_1k_queries": mean(cost_values) * 1000 if cost_values else None,
              "cost_denominator": "All recorded present queries, including queries with no relevant top-30 candidate; not the quality denominator.",
              "query_ms_median": statistics.median([r["query_ms"] for r in existing if r.get("ok") and finite(r.get("query_ms"))]) if any(r.get("ok") and finite(r.get("query_ms")) for r in existing) else None,
              "workers": sorted({r["workers"] for r in existing if "workers" in r})}
    result["present_missing"] = len(cands) - len(existing)
    result["variants"] = {}
    for variant, rows in runs.items():
        expected = [c for c in cands if c.get(variant)]
        counts = Counter(row_status(rows.get(c["qid"]), c[variant]) for c in expected)
        result["variants"][variant] = {"expected": len(expected), "recorded": sum(c["qid"] in rows for c in expected), "status_counts": dict(counts)}
    if model.startswith(QWEN_PREFIX):
        allrows = [rows[c["qid"]] for variant, rows in runs.items() for c in cands if c.get(variant) and c["qid"] in rows]
        result.update(cost_basis="gpu_time_estimate", cost_note=QWEN_COST_NOTE, latency_basis="gpu_host_wall_clock", latency_note=QWEN_LATENCY_NOTE,
                      gpu_hardware=sorted({r["extra"]["gpu"] for r in allrows if r.get("extra", {}).get("gpu")}),
                      usd_per_hour=sorted({r["extra"]["usd_per_hour"] for r in allrows if finite(r.get("extra", {}).get("usd_per_hour"))}),
                      inference_modes=dict(sorted(Counter(c.get("raw", {}).get("mode", "unavailable") for r in allrows for c in r.get("calls", []) if isinstance(c.get("raw"), dict)).items())))
    for key in METRICS:
        values = [query_models[r["qid"]][model].get("tied_top" if key == "tied_top_share" else key) for r in ok]
        result[key] = mean(v for v in values if v is not None)
    if nevir:
        return result
    both = [r for r in ok if row_status(absent.get(r["qid"]), r["absent"] or []) == "ok"]
    if both:
        signals = {"max_score": ([max(present[r["qid"]]["scores"]) for r in both], [max(absent[r["qid"]]["scores"]) for r in both])}
        if model == "jev-choice":
            for field, name, inv in [("none_prob", "1-P(none)", True), ("any_prob", "P(any)", False)]:
                if all(field in present[r["qid"]]["extra"] and field in absent[r["qid"]]["extra"] for r in both):
                    signals[name] = tuple([1 - run[r["qid"]]["extra"][field] if inv else run[r["qid"]]["extra"][field] for r in both] for run in (present, absent))
        result["nothing_relevant"] = {"n_pairs": len(both), "signals": {name: {"auroc": auroc(p, n), "threshold_keeping_90pct_answers": percentile(p, .1), "false_accept_rate": mean(x >= percentile(p, .1) for x in n), "median_present": statistics.median(p), "median_absent": statistics.median(n)} for name, (p, n) in signals.items()}}
    pairs = [(s, int(d in r["relevant"])) for r in ok for d, s in zip(present[r["qid"]]["dids"], present[r["qid"]]["scores"])]
    if pairs and all(0 <= s <= 1 for s, _ in pairs):
        bins, ece = calibration(pairs)
        result["calibration"] = {"ece": ece, "bins": bins, "is_probability_claim": model in PROB_MODELS, "n_pairs": len(pairs), "base_rate": mean(r for _, r in pairs)}
    return result


def make_rlcd_prompt(model):
    """Execute only the runner's request builders with a fake local engine.

    Importing rlcd_runner itself would import torch. AST selection avoids that and
    excludes main(), GPU setup and model loading; the engine module is an in-memory stub.
    """
    source_text = (ROOT / "rlcd_runner.py").read_text(encoding="utf-8")
    tree = ast.parse(source_text)
    functions = {"context_for", "schema_for", "score_pairs", "score_row"}
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in functions or isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id in {"QUESTION", "RUBRIC", "RUBRIC_DESC"} for t in n.targets)]
    requests = []
    class Schema:
        def __init__(self, spec):
            self.spec = spec
    def fake_engine(context, schema, temperature=1.0):
        requests.append({"function": "core.engine.run_parallel_generation", "context": context, "schema": schema.spec, "temperature": temperature})
        fields = {name: {"top_choices": [{"choice": choice, "probability": 1 / len(spec.get("choices", ["true", "false"]))} for choice in spec.get("choices", ["true", "false"])]} for name, spec in schema.spec.items()}
        return {"mode": "synthetic_prompt_capture", "elapsed_ms": 0, "prefill_ms": 0, "suffix_eval_ms": 0, "sequential_forward_passes": 2, "field_telemetry": fields}
    engine, schema = types.ModuleType("core.engine"), types.ModuleType("core.schema")
    engine.run_parallel_generation, schema.StructuredSchema = fake_engine, Schema
    namespace = {"time": types.SimpleNamespace(perf_counter=lambda: 0), "torch": types.SimpleNamespace(cuda=types.SimpleNamespace(OutOfMemoryError=MemoryError))}
    with patch.dict(sys.modules, {"core": types.ModuleType("core"), "core.engine": engine, "core.schema": schema}):
        exec(compile(ast.Module(body=selected, type_ignores=[]), "rlcd_runner.py", "exec"), namespace)
        namespace["score_row"](model.removeprefix(QWEN_PREFIX), "<QUERY>", [f"<PASSAGE_{i+1:02d}>" for i in range(30)])
    repeats = len(requests)
    if model == "qwen-rlcd-pair":
        requests = requests[:1]
    return {"id": model, "label": LABELS[model], "description": DESCRIPTIONS[model], "requests": requests, "requests_per_query": repeats,
            "source_code": "\n\n".join(ast.get_source_segment(source_text, n) for n in selected), "source_url": f"{REPO}/blob/main/rlcd_runner.py",
            "provenance": {"base_model": "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct", "port_recorded_by_runner": "https://huggingface.co/shreyansh26/Qwen-2.5-1B-RLCD", "original_recipe_recorded_by_runner": "https://huggingface.co/harshatheg/Qwen-2.5-1B-RLCD"},
            "note": "Context, schema and temperature are captured offline from the saved runner with placeholders and a mocked inference function. They are arguments to the local RLCD engine, not an HTTP request or a recovered byte-for-byte tokenizer prompt. The engine's exact package revision was not recorded in these cache rows. Synthetic answers are not exported as benchmark results. No torch import, model loading or GPU work occurs."}


def make_prompts():
    """Capture real request builders with fake responses; no network calls are possible."""
    from common import Call
    from rerankers import jev, llm_logprob, cohere, zerank
    prompts = {"schema_version": SCHEMA, "shared": {"relevance_question": RELEVANCE_QUESTION, "true_criterion": RELEVANCE_TRUE, "false_criterion": RELEVANCE_FALSE, "passage_limit_chars": MAX_CHARS}, "models": []}
    for model in MODELS:
        if model.startswith(QWEN_PREFIX):
            prompts["models"].append(make_rlcd_prompt(model))
            continue
        requests = []
        def ask(state, questions):
            requests.append({"model": jev.MODEL, "state": state, "questions": questions})
            answers = {}
            for key, q in questions.items():
                if q["type"] == "noul":
                    answers[key] = {"noul": .5}
                elif q["type"] == "choice":
                    ids = list(q["criteria"])
                    answers[key] = {"probabilities": {i: 1 / len(ids) for i in ids}, "choice": ids[0], "confidence": .5}
                else:
                    answers[key] = {"score": .5, "confidence": .5}
            body = {"answers": answers}
            return Call(0, 200, {}, 0, raw=body), body
        def post(url, headers, body, **kwargs):
            requests.append(body)
            return 500, {}, 0, {}
        instance = REGISTRY[model]()
        with patch.object(jev, "_ask", ask), patch.object(llm_logprob, "post_json", post), patch.object(cohere, "post_json", post), patch.object(zerank, "post_json", post), patch.object(llm_logprob, "_headers", lambda: {}), patch.object(cohere, "env", lambda name: "<OMITTED>"), patch.object(zerank, "env", lambda name: "<OMITTED>"):
            instance.rerank("<QUERY>", [f"<PASSAGE_{i+1:02d}>" for i in range(30)], bm25=list(range(30, 0, -1)))
        # Pair prompts vary only in the passage placeholder; retain one exact request and its repetition count.
        repeats = len(requests)
        if model in {"jev-noul-pair", "deepseek-pair"}:
            requests = requests[:1]
        prompts["models"].append({"id": model, "label": LABELS[model], "description": DESCRIPTIONS[model], "requests": requests, "requests_per_query": repeats,
                                  "source_code": inspect.getsource(type(instance).rerank), "source_url": f"{REPO}/blob/main/rerankers/{Path(inspect.getfile(type(instance))).name}",
                                  "note": "Request JSON is captured offline from the actual implementation with placeholder input and synthetic responses. Later-stage passage selections are illustrative; real selections are in query extra fields. No provider was contacted."})
    return prompts


def grouping(dataset):
    return "original8" if dataset in ENGLISH else "extra-bright" if dataset in BRIGHT else "french" if dataset == "miracl-fr" else "nevir"


def make_zip(path, entries):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 9, 16, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)


def dataset_downloads(dataset, output, entries):
    """Independent ZIP parts with their own index/attribution; each is <25 MiB."""
    shared = {name: data for name, data in entries.items() if not name.startswith("queries/")}
    shared_size = sum(len(zlib.compress(data, 6)) + 256 for data in shared.values())
    groups, group, estimate = [], {}, shared_size
    for name, data in sorted(entries.items()):
        if name in shared:
            continue
        size = len(zlib.compress(data, 6)) + 256
        if group and estimate + size > 22 * 1024 * 1024:
            groups.append(group)
            group, estimate = {}, shared_size
        group[name] = data
        estimate += size
    if group:
        groups.append(group)
    downloads = []
    for i, chunk in enumerate(groups):
        filename = f"{dataset}.zip" if len(groups) == 1 else f"{dataset}-part{i+1:02d}-of-{len(groups):02d}.zip"
        target = output / "downloads" / filename
        make_zip(target, {**shared, **chunk})
        downloads.append({"url": f"data/downloads/{filename}", "bytes": target.stat().st_size, "queries": len(chunk), "part": i + 1, "parts": len(groups)})
    # A larger snapshot can split an old single ZIP. Remove only obsolete ZIPs for
    # this exact dataset so stale downloads are not accidentally published.
    keep = {Path(d["url"]).name for d in downloads}
    for stale in [output / "downloads" / f"{dataset}.zip", *sorted((output / "downloads").glob(f"{dataset}-part*-of-*.zip"))]:
        if stale.exists() and stale.name not in keep:
            if stale.resolve().parent != (output / "downloads").resolve():
                raise ValueError("Unexpected download cleanup path")
            stale.unlink()
    return downloads


def finalize_download_notices(info, output):
    notices = encoded(license_notices())
    for download in info["downloads"]:
        path = output / download["url"].removeprefix("data/")
        with zipfile.ZipFile(path, "a", compression=zipfile.ZIP_DEFLATED) as archive:
            if "LICENSES.json" not in archive.namelist():
                entry = zipfile.ZipInfo("LICENSES.json", date_time=(2026, 9, 16, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o644 << 16
                archive.writestr(entry, notices)
            elif archive.read("LICENSES.json") != notices:
                raise ValueError("License notices changed; rebuild this dataset without --reuse-existing")
        download["bytes"] = path.stat().st_size
    info["download_bytes"] = sum(d["bytes"] for d in info["downloads"])
    # The downloadable index precedes ZIP sizes by design; the live index receives final download metadata.
    path = output / info["id"] / "index.json"
    index = json.loads(path.read_text(encoding="utf-8"))
    index["dataset"] = info
    write(path, index)


def export_dataset(dataset, output):
    cands = read_jsonl(CANDIDATES / f"{dataset}.jsonl")
    docs = {r["did"]: r["text"] for r in read_jsonl(CANDIDATES / f"{dataset}.docs.jsonl")}
    runs, superseded = {}, {}
    for model in MODELS:
        runs[model], superseded[model] = {}, {}
        for variant in ("present", "absent"):
            runs[model][variant], superseded[model][variant] = latest(model, dataset, variant)
    index = []
    query_models = {}
    pair_cands = defaultdict(list)
    if dataset == "nevir":
        for c in cands:
            pair_cands[str(c["pair"])].append(c)
    pair_results = {}
    for pid, pair in pair_cands.items():
        pair_results[pid] = {}
        for model in MODELS:
            statuses = [row_status(runs[model]["present"].get(c["qid"]), c["present"]) for c in pair]
            value = {"status": "ok" if statuses == ["ok", "ok"] else "missing" if "missing" in statuses else "failed", "correct": None, "questions_correct": None, "same_top_pick": None}
            if value["status"] == "ok":
                rs = [runs[model]["present"][c["qid"]] for c in pair]
                rights = [metrics(r, c["relevant"], True, True)["question_correct"] for r, c in zip(rs, pair)]
                value.update(correct=all(rights), questions_correct=rights, same_top_pick=order(rs[0])[0] == order(rs[1])[0])
            pair_results[pid][model] = value
    archive_entries = {}
    for c in cands:
        qid = c["qid"]
        eligible = c["n_rel_top30"] > 0
        detail = {"schema_version": SCHEMA, "dataset": dataset, "qid": qid, "query": c["query"], "eligible": eligible,
                  "relevant": c["relevant"], "relevant_total": c["n_rel_total"], "relevant_in_candidates": c["n_rel_top30"], "source": source(dataset), "variants": {}}
        imodels = {}
        for variant in ("present", "absent"):
            candidates = c.get(variant)
            if not candidates:
                detail["variants"][variant] = {"status": "not_applicable", "reason": "NevIR has no absent variant." if dataset == "nevir" else "No full absent twin was constructed for this query.", "candidates": [], "models": {}}
                continue
            exports = {model: export_row(runs[model][variant].get(qid), candidates, c["relevant"], eligible and variant == "present", dataset == "nevir") for model in MODELS}
            detail["variants"][variant] = {"status": "available", "candidates": [{"did": d["did"], "bm25": d["bm25"], "original_rank": i+1, "relevance": c["relevant"].get(d["did"], 0), "text": docs[d["did"]][:MAX_CHARS], "truncated": len(docs[d["did"]]) > MAX_CHARS, "source_url": source(dataset)["url"]} for i, d in enumerate(candidates)], "models": exports}
            if variant == "present":
                for model, ex in exports.items():
                    imodels[model] = {"status": ex["status"], **(ex["metrics"] or {k: None for k in METRICS}), "cost_usd": ex["cost_usd"], "query_ms": ex["query_ms"]}
        entry = {"qid": qid, "query": c["query"], "eligible": eligible, "relevant_total": c["n_rel_total"], "relevant_in_candidates": c["n_rel_top30"], "detail_url": detail_url(dataset, qid), "models": imodels}
        if dataset == "nevir":
            pid = str(c["pair"])
            other = next(p for p in pair_cands[pid] if p["qid"] != qid)
            detail["pair"] = {"id": pid, "qids": [p["qid"] for p in pair_cands[pid]], "other_query": {"qid": other["qid"], "query": other["query"], "detail_url": detail_url(dataset, other["qid"])}, "models": pair_results[pid]}
            entry.update(pair=pid, pair_detail_url=detail_url(dataset, qid))
            for model in MODELS:
                imodels[model]["pair_correct"] = pair_results[pid][model]["correct"]
        query_models[qid] = imodels
        index.append(entry)
        relpath = detail_url(dataset, qid).removeprefix("data/")
        write(output / relpath, detail)
        archive_entries[f"queries/{Path(relpath).name}"] = encoded(detail)
    summaries = {model: summarize_model(model, cands, runs[model], query_models, dataset == "nevir") for model in MODELS}
    if dataset == "nevir":
        for model, summary in summaries.items():
            pairs = [p[model] for p in pair_results.values()]
            ok = [p for p in pairs if p["status"] == "ok"]
            summary.update(pairs=len(ok), pairs_total=len(pairs), pairs_missing=sum(p["status"] == "missing" for p in pairs), pairs_failed=sum(p["status"] == "failed" for p in pairs),
                           paired_accuracy=mean(p["correct"] for p in ok), question_accuracy=mean(q for p in ok for q in p["questions_correct"]), same_top_pick_share=mean(p["same_top_pick"] for p in ok))
    info = {"id": dataset, "label": LABEL_DATASETS.get(dataset, "BRIGHT " + dataset.removeprefix("bright-").replace("_", " ").title()), "group": grouping(dataset), "language": "French" if dataset == "miracl-fr" else "English", "queries_total": len(cands), "queries_eligible": sum(c["n_rel_top30"] > 0 for c in cands), "models": summaries, "source": source(dataset), "index_url": f"data/{dataset}/index.json", "download_url": f"data/downloads/{dataset}.zip", "superseded_rows": superseded}
    timestamps = sorted(r["ts"] for model in runs.values() for rows in model.values() for r in rows.values() if r.get("ts"))
    info["recorded_range"] = {"first": timestamps[0], "last": timestamps[-1]} if timestamps else None
    if dataset == "nevir":
        info["pairs_total"] = len(pair_cands)
    index_obj = {"schema_version": SCHEMA, "dataset": info, "queries": index}
    write(output / dataset / "index.json", index_obj)
    archive_entries["index.json"] = encoded(index_obj)
    archive_entries["ATTRIBUTION.json"] = encoded(source(dataset))
    info["downloads"] = dataset_downloads(dataset, output, archive_entries)
    info["download_url"] = info["downloads"][0]["url"]
    info["download_bytes"] = sum(d["bytes"] for d in info["downloads"])
    print(f"{dataset}: {len(cands)} queries, {info['queries_eligible']} eligible, download {info['download_bytes']/1048576:.2f} MiB", flush=True)
    return info


def aggregate(group_id, label, datasets):
    out = {"id": group_id, "label": label, "dataset_ids": [d["id"] for d in datasets], "queries_total": sum(d["queries_total"] for d in datasets), "queries_eligible": sum(d["queries_eligible"] for d in datasets), "models": {}}
    for model in MODELS:
        rows = [d["models"][model] for d in datasets]
        scored = [r for r in rows if r["n"]]
        cost_queries = sum(r["cost_queries"] for r in rows)
        cost = sum(r["cost_usd_present"] or 0 for r in rows)
        n = sum(r["n"] for r in scored)
        macro = {k: mean(r[k] for r in scored if r[k] is not None) for k in METRICS}
        micro = {k: sum(r[k] * r["n"] for r in scored if r[k] is not None) / sum(r["n"] for r in scored if r[k] is not None) if any(r[k] is not None for r in scored) else None for k in METRICS}
        result = {**macro, "macro": macro, "query_weighted": micro, "n": n, "datasets": len(scored), "datasets_expected": len(datasets), "coverage_complete": all(r["coverage_complete"] for r in rows), "cost_queries": cost_queries, "cost_usd_present": cost if cost_queries else None, "cost_per_1k_queries": cost / cost_queries * 1000 if cost_queries else None, "missing": sum(r["missing"] for r in rows), "failed": sum(r["failed"] for r in rows), "queries_total": out["queries_total"], "queries_eligible": out["queries_eligible"]}
        if model.startswith(QWEN_PREFIX):
            result.update(cost_basis="gpu_time_estimate", cost_note=QWEN_COST_NOTE, latency_basis="gpu_host_wall_clock", latency_note=QWEN_LATENCY_NOTE)
        if group_id == "nevir":
            result.update({k: rows[0][k] for k in ("paired_accuracy", "question_accuracy", "pairs", "pairs_total", "pairs_missing", "pairs_failed", "same_top_pick_share")})
        out["models"][model] = result
    return out


def batching_export(output):
    raw = json.loads((ROOT / "results" / "batching.json").read_text(encoding="utf-8"))
    # This file only stores billing/crosstalk summaries, not raw batched responses.
    result = {"schema_version": SCHEMA, **raw, "per_query_outputs_available": False, "limitation": "The original batching script saved aggregate metrics and billing samples only. Per-query packed scores and raw responses were not persisted and cannot be reconstructed from these records.", "input_samples": []}
    cands = [c for c in read_jsonl(CANDIDATES / "scifact.jsonl") if c["n_rel_top30"] > 0][:raw["queries"]]
    docs = {r["did"]: r["text"] for r in read_jsonl(CANDIDATES / "scifact.docs.jsonl")}
    module = ast.parse((ROOT / "batching.py").read_text(encoding="utf-8"))
    selected = ast.Module(body=[n for n in module.body if isinstance(n, ast.FunctionDef) and n.name in {"packed_questions", "pack"}], type_ignores=[])
    namespace = {"RELEVANCE_TRUE": RELEVANCE_TRUE, "RELEVANCE_FALSE": RELEVANCE_FALSE, "docs": docs, "truncate": lambda text: text[:MAX_CHARS]}
    exec(compile(selected, "batching.py", "exec"), namespace)
    for k in (1, 2, 3, 4):
        state, questions, _ = namespace["pack"](cands[:k])
        result["input_samples"].append({"k": k, "qids": [c["qid"] for c in cands[:k]], "status": "reconstructed_input_only", "request": {"model": "jev-latest", "state": state, "questions": questions}, "source": source("scifact")})
    result["exact_prompt_source"] = "\n\n".join(ast.get_source_segment((ROOT / "batching.py").read_text(encoding="utf-8"), n) for n in module.body if isinstance(n, ast.FunctionDef) and n.name in {"packed_questions", "pack"})
    write(output / "batching.json", result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=PUBLIC)
    parser.add_argument("--datasets", nargs="*", default=list(DATASETS) + ["nevir"])
    parser.add_argument("--reuse-existing", action="store_true", help="Finalize metadata from a previous complete export; verifies every candidate and cache input hash before reuse.")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    prompt = make_prompts()
    write(output / "prompts.json", prompt)
    batching_export(output)
    if args.reuse_existing:
        previous = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        hashes = json.loads((output / "provenance.json").read_text(encoding="utf-8"))["inputs_sha256"]
        for dataset in args.datasets:
            required = [*CANDIDATES.glob(f"{dataset}*.jsonl"), *CACHE.glob(f"*/{dataset}.*.jsonl*")]
            for path in required:
                if hashes.get(path.relative_to(ROOT).as_posix()) != hashlib.sha256(path.read_bytes()).hexdigest():
                    raise ValueError(f"Input changed or was not exported: {path.relative_to(ROOT).as_posix()}")
        by_id = {d["id"]: d for d in previous["datasets"]}
        datasets = [by_id[d] for d in args.datasets]
    else:
        datasets = [export_dataset(d, output) for d in args.datasets]
    write(output / "licenses.json", license_notices())
    for dataset in datasets:
        finalize_download_notices(dataset, output)
    groups = [aggregate(gid, label, [d for d in datasets if d["group"] == gid]) for gid, label in [("original8", "Original eight retrieval datasets"), ("extra-bright", "Five additional BRIGHT subsets"), ("french", "French transfer"), ("nevir", "NevIR negation pairs")] if any(d["group"] == gid for d in datasets)]
    input_files = sorted(set([ROOT / "common.py", ROOT / "eval.py", ROOT / "batching.py", ROOT / "rlcd_runner.py", ROOT / "results" / "batching.json", Path(__file__).resolve(), *list((ROOT / "rerankers").glob("*.py")), *[p for d in args.datasets for p in CANDIDATES.glob(f"{d}*.jsonl")], *[p for d in args.datasets for p in CACHE.glob(f"*/{d}.*.jsonl*")]]))
    input_hashes = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in input_files}
    version = hashlib.sha256(encoded(input_hashes)).hexdigest()[:16]
    methodology = {"ranking_population": "Only queries with at least one positively labeled passage in the BM25 top-30 and a complete valid score vector are scored for retrieval quality. All original queries remain browsable.", "ndcg": "nDCG@10 uses linear relevance gain and ideal DCG over all positive query labels, not just the candidate pool.", "tie_break": "Descending scores, stable original BM25 candidate order. The reverse-order tie sensitivity column reverses original candidate order inside ties; this can raise or lower the metric and is not a statistical bound.", "weighting": "Macro gives each dataset equal weight. Query-weighted weights each dataset by the model's scored query count. Missing configurations are null and excluded; coverage counts are displayed.", "cost": "Present-only latest recorded cost divided by all recorded present queries, including queries without a relevant top-30 candidate; no absent-variant cost in the headline. Partial coverage is shown. List prices are the benchmark's recorded prices, not a current quotation.", "latency": "Observed wall-clock time for the recorded query. Includes network, sequential subrequests and any retries. It is not server-only inference time or a throughput benchmark; workers are retained per query.", "absent": "All positively labeled passages removed and candidates refilled from further down BM25. A zero relevance value means no positive label; it does not establish factual irrelevance.", "nevir": "Separate paired accuracy: both questions must strictly favor their relevant passage. Ties count as wrong. The two passages retain fixed passage order at input. Never included in retrieval means.", "cache": "Gzipped rows first, plain rows second; the last row for each query ID wins. Superseded attempt counts are disclosed. This is a snapshot, not a reproducibility claim for mutable provider aliases.", "publishing": "Sanitized allowlisted outputs and exact 2,000-character candidate snippets only. No credentials, headers, request IDs, private files or whole corpora.", "batching": "Saved aggregate observations and reconstructed input examples only. Original per-query batched outputs were not retained."}
    methodology["qwen_cost"] = QWEN_COST_NOTE
    methodology["latency"] = "Hosted API latency is observed client wall-clock query time, including network and sequential subrequests. Qwen RLCD latency is wall-clock model-call time on the GPU host; its per-pair mode includes all sequential prompts. These timings have different measurement boundaries and are not a throughput or like-for-like service-latency comparison."
    methodology["qwen_scope"] = "Qwen follow-up configurations use the same saved candidate lists, positive relevance labels, 2,000-character passage limit and stable original-order tie handling. Missing French or other unrecorded configurations remain unavailable, not zero. Cached allowed-label probabilities are preserved at their recorded precision. The engine mode records when fields were processed in smaller chunks after a GPU memory failure."
    methodology["order_diagnostics"] = "The reversed-input configurations are order-sensitivity diagnostics, not independent models or separately trained alternatives. Their saved scores remain inspectable and have been mapped back to the original candidate order before metrics are computed."
    metadata = []
    for model in MODELS:
        entry = model_metadata(model)
        available = [d["id"] for d in datasets if d["models"][model]["present_recorded"]]
        missing = [d["id"] for d in datasets if not d["models"][model]["present_recorded"]]
        entry.update(available_datasets=available, unavailable_datasets=missing,
                     coverage_note=f"Recorded present results in {len(available)} of {len(datasets)} datasets." + (" No recorded results for: " + ", ".join(missing) + "." if missing else ""))
        metadata.append(entry)
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = None
    recorded_ranges = [d["recorded_range"] for d in datasets if d.get("recorded_range")]
    recorded_range = {"first": min(r["first"] for r in recorded_ranges), "last": max(r["last"] for r in recorded_ranges)} if recorded_ranges else None
    prices = {**PRICES, "qwen-rlcd": {"usd_per_hour_recorded": sorted({rate for d in datasets for m, r in d["models"].items() if m.startswith(QWEN_PREFIX) for rate in r.get("usd_per_hour", [])}), "source": "GPU hourly rate saved in each Qwen cache row (extra.usd_per_hour), not a current price lookup.", "basis": QWEN_COST_NOTE}}
    manifest = {"schema_version": SCHEMA, "version": version, "title": "Jev reranking evidence", "provenance": {"repository_url": REPO, "repository_visibility": "public", "benchmark_commit": commit, "recorded_date": "2026-09-16", "recorded_range": recorded_range, "original_api_run_date": "2026-09-16", "snapshot_updated_date": "2026-09-17", "followup_note": "The Qwen follow-up was added to the lab on September 17. Saved Qwen timestamps are September 16 UTC; the snapshot publication date does not relabel the measurements.", "selection": "latest row per query ID", "input_hashes_url": "data/provenance.json"}, "methodology": methodology, "models": metadata, "groups": groups, "datasets": datasets, "prompts_url": "data/prompts.json", "batching_url": "data/batching.json", "licenses_url": "data/licenses.json", "prices_recorded": prices}
    write(output / "provenance.json", {"schema_version": SCHEMA, "version": version, "inputs_sha256": input_hashes})
    write(output / "manifest.json", manifest)
    files = [p for p in output.rglob("*") if p.is_file()]
    too_large = [p for p in files if p.stat().st_size >= 25 * 1024 * 1024]
    if too_large:
        raise SystemExit("Asset exceeds 25 MiB: " + ", ".join(p.name for p in too_large))
    print(f"Exported {len(files)} files, {sum(p.stat().st_size for p in files)/1048576:.2f} MiB, version {version}")


if __name__ == "__main__":
    main()
