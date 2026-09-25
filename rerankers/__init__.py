"""Registry of every reranker under test. Each takes (query, docs) and returns a QueryResult with one score per doc."""
from __future__ import annotations

# The same judgement wording goes to every model that takes an instruction (Jev and the LLM baseline).
RELEVANCE_QUESTION = "Does the passage contain the information needed to answer or verify the query?"
RELEVANCE_TRUE = "The passage states or directly implies the answer to the query, or the evidence that verifies it."
RELEVANCE_FALSE = "The passage is only on a related topic; it does not supply what the query asks for."

from .bm25 import BM25Order  # noqa: E402
from .cohere import Cohere  # noqa: E402
from .jev import (JevCascade, JevChoice, JevChoiceReversed, JevDuel, JevNoulBatch, JevNoulPair,  # noqa: E402
                  JevScoreBatch, JevTournament)
from .llm_logprob import LLMJsonScores, LLMYesProb  # noqa: E402
from .zerank import Zerank  # noqa: E402

REGISTRY = {
    "bm25": lambda: BM25Order(),
    "jev-noul-pair": lambda: JevNoulPair(),
    "jev-noul-batch": lambda: JevNoulBatch(),
    "jev-choice": lambda: JevChoice(),
    "jev-score-batch": lambda: JevScoreBatch(),
    "jev-duel": lambda: JevDuel(),
    "jev-tournament": lambda: JevTournament(),
    "jev-cascade": lambda: JevCascade(),
    "jev-choice-reversed": lambda: JevChoiceReversed(),
    "cohere-pro": lambda: Cohere("cohere/rerank-4-pro", "cohere-pro"),
    "cohere-fast": lambda: Cohere("cohere/rerank-4-fast", "cohere-fast"),
    "zerank-2": lambda: Zerank("zerank-2"),
    # DeepSeek V4.1 Flash on DeepSeek's own API (the reference host; the model's released weights are fp8-native),
    # thinking switched off. Two ways, mirroring Jev's per-pair and one-call modes.
    "deepseek-pair": lambda: LLMYesProb("deepseek/deepseek-v4.1-flash", "deepseek-pair", provider="DeepSeek"),
    "deepseek-json": lambda: LLMJsonScores("deepseek/deepseek-v4.1-flash", "deepseek-json", provider="DeepSeek"),
}

# System One servers from models.yaml: one model key per entry and mode, <name>-<mode>, asked through systemone.py.
from .registry import load as _load_models  # noqa: E402
from .systemone import make as _make  # noqa: E402

MODELS = _load_models()
for _entry in MODELS.values():
    if _entry.name in REGISTRY:
        raise SystemExit(f"models.yaml: {_entry.name} is already a built-in model key; pick another name")
    for _key in _entry.keys:
        if _key in REGISTRY:
            raise SystemExit(f"models.yaml: {_entry.name} would run as {_key}, which already exists; pick another name")
        _mode = next(s.mode for s in _entry.steps if s.key == _key)
        REGISTRY[_key] = lambda e=_entry, m=_mode, k=_key: _make(e.endpoint, m, k)
KEY_ENTRY = {k: e for e in MODELS.values() for k in e.keys}
