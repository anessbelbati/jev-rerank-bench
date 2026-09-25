"""models.yaml: the System One servers under test, one entry per model, and what each one runs.

Each entry becomes one run.py model per mode, named <name>-<mode> (also its cache folder), asked through
rerankers/systemone.py. A mode that needs more passages in one request than the server takes, or more tokens than its
window, runs its one-passage form instead (FALLBACK): score-batch becomes score-pair, every other multi-passage mode
becomes noul-pair. What a mode needs is the largest request it sent Jev on this benchmark (results/request_sizes.json,
from scripts/request_sizes.py).

    uv run run.py --model <name> --plan        # an entry's plan: what runs, and why
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass

import yaml

from common import RESULTS, ROOT

from .systemone import MODES, Endpoint

MODELS_FILE = ROOT / "models.yaml"
SIZES_FILE = RESULTS / "request_sizes.json"
FALLBACK = {"noul-batch": "noul-pair", "choice": "noul-pair", "choice-reversed": "noul-pair", "duel": "noul-pair",
            "tournament": "noul-pair", "cascade": "noul-pair", "score-batch": "score-pair"}
REQUIRED = ("base_url", "model", "modes", "max_context", "passages_per_request", "concurrency")
OPTIONAL = ("key_env", "price", "label", "serve", "runs_on")
PRICE_FIELDS = ("gpu_usd_per_hour", "input_per_m", "output_per_m")
NAME = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


@dataclass(frozen=True)
class Step:
    asked: str      # the mode as listed in models.yaml
    mode: str       # the mode that runs
    key: str        # its run.py model key and cache folder
    note: str       # what it needs, and why it changed if it did


@dataclass(frozen=True)
class Entry:
    name: str
    endpoint: Endpoint
    max_context: int
    passages_per_request: int
    concurrency: int
    steps: tuple[Step, ...]
    label: str = ""
    serve: str = ""
    runs_on: str = ""

    @property
    def keys(self) -> list[str]:
        return list(dict.fromkeys(s.key for s in self.steps))


def sizes() -> dict:
    if not SIZES_FILE.exists():
        raise SystemExit(f"{SIZES_FILE} is missing: run `uv run scripts/request_sizes.py` (it reads the saved Jev runs)")
    return json.loads(SIZES_FILE.read_text(encoding="utf-8"))["modes"]


def plan(name: str, modes: list[str], max_context: int, passages_per_request: int, need: dict) -> tuple[Step, ...]:
    steps = []
    for asked in modes:
        mode, why = asked, ""
        n = need[asked]
        if n["passages"] > passages_per_request or n["max_input_tokens"] > max_context:
            if asked in FALLBACK:
                why = (f"the server takes {passages_per_request} passage(s) per request" if n["passages"] > passages_per_request
                       else f"its window ({max_context:,} tokens) is smaller than this mode's largest request ({n['max_input_tokens']:,})")
                mode = FALLBACK[asked]
                n = need[mode]
        note = f"{n['passages']} passage(s) per request, largest request {n['max_input_tokens']:,} tokens"
        if why:
            note = f"runs as {mode}: {why}; {note}"
        if n["max_input_tokens"] > max_context:
            note += (f"; WARNING: requests over {max_context:,} tokens will fail or be cut by the server "
                     f"({n['p99_input_tokens']:,} tokens covers 99% of them)")
        steps.append(Step(asked, mode, f"{name}-{mode}", note))
    return tuple(steps)


def _positive_int(name: str, field: str, v) -> int:
    if not isinstance(v, int) or isinstance(v, bool) or v < 1:
        raise SystemExit(f"models.yaml, {name}: {field} must be a whole number of at least 1 (got {v!r})")
    return v


def _entry(name: str, e: dict, need: dict) -> Entry:
    if not NAME.match(str(name)):
        raise SystemExit(f"models.yaml: entry name {name!r} must be lowercase letters, digits, '.', '_' or '-' (it names cache folders)")
    if not isinstance(e, dict):
        raise SystemExit(f"models.yaml, {name}: expected the fields {', '.join(REQUIRED)}")
    unknown = sorted(set(e) - set(REQUIRED) - set(OPTIONAL))
    missing = [f for f in REQUIRED if f not in e]
    if unknown or missing:
        raise SystemExit(f"models.yaml, {name}: " + "; ".join(filter(None, [
            f"unknown field(s) {', '.join(unknown)}" if unknown else "", f"missing {', '.join(missing)}" if missing else ""])))
    modes = e["modes"]
    if not isinstance(modes, list) or not modes or any(m not in MODES for m in modes):
        raise SystemExit(f"models.yaml, {name}: modes must be a list drawn from {', '.join(MODES)} (got {modes!r})")
    price = e.get("price") or {}
    if not isinstance(price, dict) or set(price) - set(PRICE_FIELDS) or any(
            not isinstance(v, (int, float)) or isinstance(v, bool) or v < 0 for v in price.values()):
        raise SystemExit(f"models.yaml, {name}: price takes {', '.join(PRICE_FIELDS)}, each a number of at least 0 (got {price!r})")
    for f in ("base_url", "model"):
        if not isinstance(e[f], str) or not e[f].strip():
            raise SystemExit(f"models.yaml, {name}: {f} must be text")
    if e.get("key_env") is not None and not (isinstance(e["key_env"], str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", e["key_env"])):
        raise SystemExit(f"models.yaml, {name}: key_env is the NAME of the .env entry holding the key (e.g. MY_API_KEY), never the key")
    max_context = _positive_int(name, "max_context", e["max_context"])
    passages = _positive_int(name, "passages_per_request", e["passages_per_request"])
    concurrency = _positive_int(name, "concurrency", e["concurrency"])
    # For a pod run of one entry: the server copy this process talks to, and the pod's rate per copy.
    gpu = os.environ.get("SYSTEMONE_GPU_RATE") or price.get("gpu_usd_per_hour")
    endpoint = Endpoint(os.environ.get("SYSTEMONE_BASE_URL") or e["base_url"], e["model"], e.get("key_env") or None,
                        float(price.get("input_per_m", 0.0)), float(price.get("output_per_m", 0.0)),
                        float(gpu) if gpu is not None else None)
    return Entry(name, endpoint, max_context, passages, concurrency, plan(name, modes, max_context, passages, need),
                 str(e.get("label") or ""), str(e.get("serve") or ""), str(e.get("runs_on") or ""))


def load(path=MODELS_FILE) -> dict[str, Entry]:
    if not path.exists():
        return {}
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    models = doc.get("models") or {}
    if not isinstance(models, dict):
        raise SystemExit("models.yaml: expected a top-level 'models:' mapping of name -> fields")
    need = sizes() if models else {}
    return {str(name): _entry(str(name), e, need) for name, e in models.items()}


def describe(entry: Entry) -> list[str]:
    ep = entry.endpoint
    price = (f"GPU time at ${ep.gpu_usd_per_hour}/h" if ep.gpu_usd_per_hour is not None
             else f"${ep.input_per_m}/M in, ${ep.output_per_m}/M out, or the reply's usage.cost")
    lines = [f"{entry.name}: {entry.label or ep.model}",
             f"  POST {ep.url}  model {ep.model}  key {ep.key_env or '(none)'}  {entry.concurrency} at a time  {price}",
             f"  window {entry.max_context:,} tokens, up to {entry.passages_per_request} passage(s) per request"]
    seen = set()
    for s in entry.steps:
        dup = " (already planned)" if s.key in seen else ""
        seen.add(s.key)
        lines.append(f"  {s.asked:16} -> {s.key}{dup}: {s.note}")
    return lines
