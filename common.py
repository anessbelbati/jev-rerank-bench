"""Shared pieces: paths, published prices, passage truncation, HTTP with backoff, and the raw-response cache.

Every reranker sees the same 30 candidates cut to the same MAX_CHARS, and every API response is appended verbatim to
cache/<model>/<dataset>.<variant>.jsonl so a rerun costs nothing and anyone can audit the raw outputs.
"""
from __future__ import annotations

import gzip
import json
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
DATA = ROOT / "data"
CANDIDATES = ROOT / "candidates"
CACHE = ROOT / "cache"
RESULTS = ROOT / "results"

TOP_K = 30          # candidates per query; every model reranks the same 30
MAX_CHARS = 2000    # passage truncation applied identically to every model (about 400-500 tokens)
BRIGHT = ("bright-biology", "bright-economics", "bright-earth_science", "bright-psychology", "bright-robotics", "bright-stackoverflow", "bright-sustainable_living")
DATASETS = ("scifact", "fiqa", "nq", "nfcorpus", "trec-covid") + BRIGHT + ("csn-python", "miracl-fr")
EXTRA = ("nevir",)      # negation pairs: two passages per question, scored by paired accuracy, never in the averages
ENGLISH = ("scifact", "fiqa", "nq", "nfcorpus", "trec-covid", "bright-biology", "bright-economics", "csn-python")   # the pre-registered headline; the five later BRIGHT subsets are reported as their own block
VARIANTS = ("present", "absent")   # absent = every relevant passage removed from the 30, refilled from further down BM25

# Published list prices, USD. Each run's cost is the API's own usage field times the price below (OpenRouter returns
# the exact billed amount itself). Sources and the day they were read are kept next to the number.
PRICES = {
    "jev": {"input_per_m": 0.042, "output_per_m": 0.0,
            "source": "typesafe.ai/blog/introducing-system-one-models-and-jev, read 2026-09-16: $0.042/MTok input, output free"},
    "cohere-pro": {"per_search": 0.0025,
                   "source": "billed through OpenRouter's rerank endpoint, which returns usage.cost per call ($0.0025 per search unit, "
                             "verified 2026-09-16); one search = one query + up to 100 documents, documents over 500 tokens count as extra chunks"},
    "cohere-fast": {"per_search": 0.002, "source": "billed through OpenRouter's rerank endpoint, usage.cost per call ($0.002 per search unit, verified 2026-09-16)"},
    "zerank-2": {"per_m_tokens": 0.025, "source": "zeroentropy.dev/pricing, read 2026-09-16: $0.025 per million tokens"},
    "openrouter": {"source": "usage.cost field returned by OpenRouter on every request (usage.include=true)"},
}


def env(name: str) -> str:
    v = os.environ.get(name, "").strip()
    if not v:
        raise SystemExit(f"{name} is missing from {ROOT / '.env'}")
    return v


def truncate(text: str) -> str:
    return text if len(text) <= MAX_CHARS else text[:MAX_CHARS]


@dataclass
class Call:
    latency_ms: float
    status: int
    usage: dict
    cost_usd: float
    raw: dict | str | None = None
    error: str | None = None


@dataclass
class QueryResult:
    scores: list[float | None]          # aligned with the candidate list; None = that candidate got no score
    calls: list[Call]
    extra: dict = field(default_factory=dict)   # e.g. Jev's P(none) and "any passage relevant?" probability

    @property
    def cost_usd(self) -> float:
        return sum(c.cost_usd for c in self.calls)

    @property
    def ok(self) -> bool:
        return all(s is not None for s in self.scores)


RETRY_STATUSES = {408, 409, 425, 429, 500, 502, 503, 504, 529}
_local = threading.local()


def _session() -> requests.Session:
    s = getattr(_local, "session", None)
    if s is None:
        s = requests.Session()
        _local.session = s
    return s


def post_json(url: str, headers: dict, body: dict, *, timeout: float = 90.0, retries: int = 6):
    """POST with exponential backoff on rate limits and overloads.

    Returns (status, parsed body or text, latency_ms of the final attempt, response headers). Latency is the wall
    clock of one HTTP round trip from this machine, so it includes the network path from Algeria.
    """
    last = (0, "no attempt made", 0.0, {})
    for attempt in range(retries):
        if attempt:
            time.sleep(min(30.0, 1.5 * 2 ** (attempt - 1)))
        t = time.perf_counter()
        try:
            r = _session().post(url, headers=headers, json=body, timeout=timeout)
        except requests.RequestException as e:
            last = (0, str(e), (time.perf_counter() - t) * 1000, {})
            continue
        ms = (time.perf_counter() - t) * 1000
        try:
            parsed = r.json()
        except ValueError:
            parsed = r.text
        if r.status_code in RETRY_STATUSES:
            ra = r.headers.get("Retry-After", "")
            if ra.isdigit():
                time.sleep(min(60, int(ra)))
            last = (r.status_code, parsed, ms, dict(r.headers))
            continue
        return r.status_code, parsed, ms, dict(r.headers)
    return last


class Cache:
    """One JSONL file per (model, dataset, variant); one line per query, holding every raw response."""

    def __init__(self, model_key: str, dataset: str, variant: str):
        self.path = CACHE / model_key / f"{dataset}.{variant}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self.rows: dict[str, dict] = {}
        # The public repo ships the raw responses gzipped; new rows are appended to the plain file and win on qid.
        for row in read_jsonl(self.path):
            self.rows[row["qid"]] = row

    def has(self, qid: str) -> bool:
        return qid in self.rows

    def put(self, row: dict) -> None:
        with self._lock:
            self.rows[row["qid"]] = row
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")


def jsonl_exists(path: Path) -> bool:
    return path.exists() or path.with_name(path.name + ".gz").exists()


def read_jsonl(path: Path) -> list[dict]:
    """Rows of <path>.gz (if present) followed by rows of <path> (if present); either may be missing."""
    rows: list[dict] = []
    gz = path.with_name(path.name + ".gz")
    if gz.exists():
        with gzip.open(gz, "rt", encoding="utf-8") as f:
            rows += [json.loads(l) for l in f if l.strip()]
    if path.exists():
        with path.open(encoding="utf-8") as f:
            rows += [json.loads(l) for l in f if l.strip()]
    return rows


def write_jsonl(path: Path, rows) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
