# jev-rerank-bench

Can a decision model beat dedicated rerankers? A reproducible benchmark of **TypeSafe Jev** (`jev-latest`, 1.13.0)
against **Cohere Rerank 4** (Pro and Fast), **ZeroEntropy zerank-2**, a **cheap chat model** (DeepSeek V4.1 Flash,
thinking off) used two ways as the "it's just a classifier" baseline, and plain **BM25** as the floor.

Eight public English datasets in the headline, five more BRIGHT subsets as a reasoning block, NevIR for negation, and
MIRACL French as a side test. Every model reranks the same 30 keyword-search candidates per question. Every raw API
response is in `cache/`, every gap in the write-up comes with a bootstrap range, and every number is produced by a
script in this repo.

## Headline (8 English datasets, 1,617 scored questions, each dataset counts once)

| Model | nDCG@10 | Top pick right | Time per query | $ per 1,000 queries | Spots "nothing here" (AUROC) |
|---|---|---|---|---|---|
| Jev 4-level rubric, 30 in one call | 0.692 | 74% | 422 ms | 0.45 | 0.75 |
| Cohere Rerank 4 Pro | 0.691 | 73% | 844 ms | 2.51 | 0.78 |
| Jev 30 yes/no in one call | 0.685 | 72% | 396 ms | 0.41 | 0.75 |
| Jev one Choice + none | 0.684 | 76% | 338 ms | 0.33 | 0.72 |
| Cohere Rerank 4 Fast | 0.684 | 72% | 726 ms | 2.01 | 0.75 |
| ZeroEntropy zerank-2 | 0.682 | 72% | 1.8 s | 0.22 | 0.74 |
| DeepSeek V4.1 Flash JSON, 30 in one call | 0.682 | 73% | 2.2 s | 1.13 | 0.75 |
| Jev cascade (batch prune, then 8 pairs) | 0.674 | 69% | 2.5 s | 0.63 | 0.73 |
| Jev yes/no per pair | 0.670 | 70% | 8.2 s | 0.81 | 0.73 |
| Jev tournament (6 groups, then final) | 0.668 | 75% | 641 ms | 0.43 | 0.71 |
| DeepSeek V4.1 Flash P(yes) per pair | 0.608 | 62% | 34.3 s | 1.38 | 0.65 |
| Jev 45 duels in one call (top 10) | 0.580 | 66% | 324 ms | 0.21 | 0.65 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | 0.340 | 30% | 419 ms | 0.09 | 0.55 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | 0.255 | 22% | 360 ms | 0.08 | 0.52 |
| BM25 (floor) | 0.486 | 45% | – | 0 | 0.58 |

- Ranking quality: Jev rubric and Cohere Pro are tied (gap +0.1 points, 95% range −0.9 to +1.2 over 10,000 paired
  resamples of the questions).
- Top pick: Jev one Choice is ahead of every dedicated reranker (vs Cohere Pro +3.1 points, range +0.7 to +5.6).
- Negation (NevIR, 1,383 pairs): Jev rubric 71% of pairs right, Cohere Pro 67% (gap +4.2, range +1.5 to +6.9),
  ZeroEntropy 61%; the chat-model baseline 17–22%, below the 25% of guessing.
- Reasoning (7 BRIGHT subsets, 307 questions): Jev rubric first on average (0.493 vs 0.487), within noise.
- The open-source "Qwen-2.5-1B-RLCD" recipe (Qwen2.5-1.5B, no training, all 30 keys scored in one batched pass), run with its own
  inference code on rented RTX 4090s: below the BM25 floor in both modes (Jev rubric ahead by +35.2 points, range +33.2 to +37.4,).
  Its yes/no score separates relevant from irrelevant passages by only 0.046 (Jev, same wording: 0.429) and drifts with
  position (0.195, at slot 1, 0.384 at slot 30). NevIR: 7% and 19% of pairs, below the 25% of guessing. `rlcd_check.py` has the check.
- Where Jev loses, and it is real: FiQA (Cohere Pro by 5.0 points), Natural Questions (by 3.9), TREC-COVID
  (ZeroEntropy by 2.1, barely), French (Cohere Pro by 6.4).

Full tables, per-dataset numbers, latency percentiles, usage totals and every check: `results/summary.md`,
`results/*.json`, and the charts in `results/`.

## What is measured

- **Ranking:** nDCG@10, Top-1, Recall@5, MRR@10 over the questions whose BM25 top-30 holds at least one relevant
  passage (a reranker can reorder, it cannot conjure). Ties in a model's scores keep BM25 order for every model; the
  worst-case reading (ties broken against the model) is reported too, because two models hand out many identical scores.
- **Speed:** one HTTP round trip from Algiers, median and p95, at the stated concurrency. `network.py` measures the
  bare connection time (~200 ms to all three hosts) and Jev's own server-side time from its response header
  (110–150 ms on 30 passages), so the network share is known.
- **Cost:** each API's own usage field × its list price; OpenRouter returns the exact billed amount per call.
- **The "nothing relevant" test:** for every question, a twin list with every relevant passage removed and refilled
  from further down BM25. AUROC of the top score, and the false-accept rate at 90% recall. For Jev also its built-in
  `none` option and its "does any passage answer it?" question.
- **Calibration:** ECE and reliability curves for the models whose scores are probabilities.
- **Noise:** `significance.py` resamples the questions 10,000 times (paired across models) and reports a 95% range
  and a p-value for every gap; the write-up calls a gap "real" only if the range excludes zero.
- **Jev under the microscope:** TypeSafe's confidence bands against real answers, order sensitivity (same 30 passages
  reversed), repeat drift (same request twice), cold start after 1–15 minutes idle, and `batching.py`: what one extra
  question costs when several ride on the same passages (~443 tokens, 4% of the passages), the request-size ceiling
  (~33,700 tokens), and whether answers change when questions share a state.
- **Negation:** `nevir_eval.py` scores NevIR by paired accuracy (both questions of a pair right, ties wrong).

## Datasets

| Dataset | Domain | Source | Queries | Corpus | Scored* |
|---|---|---|---|---|---|
| SciFact | scientific claims | BEIR, test | 300 | 5,183 abstracts | 264 |
| FiQA-2018 | finance questions | BEIR, test | 648 | 57,638 passages | 411 |
| Natural Questions | real Google searches → Wikipedia | BEIR, test, 500 sampled (seed 0) | 500 | 2,681,468 passages | 320 |
| NFCorpus | medical / nutrition | BEIR, test | 323 | 3,633 documents | 239 |
| TREC-COVID | COVID-19 literature | BEIR, test | 50 | 171,332 papers | 50 |
| BRIGHT biology / economics | reasoning-intensive StackExchange | MTEB `BrightRetrieval` | 103 / 103 | 57,359 / 50,220 | 39 / 38 |
| CodeSearchNet Python | docstring → function | MTEB `CodeSearchNetRetrieval`, 300 sampled | 300 | 1,000 functions | 256 |
| BRIGHT earth science / psychology / robotics / StackOverflow / sustainable living | run after the headline was fixed; reported as their own block | MTEB `BrightRetrieval` | 116 / 101 / 101 / 117 / 108 | 50–60k each | 57 / 29 / 35 / 62 / 47 |
| NevIR | negation pairs, two questions each; paired accuracy, never in the averages | `orionweller/NevIR`, test | 2,766 (1,383 pairs) | 2 per question | 2,766 |
| MIRACL French | French Wikipedia questions (side test) | MTEB `MIRACLReranking` fr/dev | 269 | 100-passage pool per query | 152 |

\* questions whose BM25 top-30 holds at least one relevant passage.

**Candidates.** BM25 (`bm25s`, Snowball stemmer, language stopwords) top 30 per question over the whole corpus (for
MIRACL, over the 100-passage pool MTEB ships per query). Every model gets the exact same 30, cut to the same 2,000
characters. The vendors' own reports rerank the top 100 from an embedding retriever; this is a shallower, keyword-based
first stage, stated as such. (100 passages at 2,000 characters is ~35,000 tokens, above Jev's request ceiling.)

## Models and how each is asked

| key | model | how |
|---|---|---|
| `bm25` | BM25 order | the floor; no API |
| `cohere-pro` / `cohere-fast` | Cohere `rerank-4-pro` / `rerank-4-fast` via OpenRouter's rerank endpoint (exact billed cost per call) | one call per query, 30 documents |
| `zerank-2` | ZeroEntropy `zerank-2` | one `POST /v1/models/rerank` per query, 30 documents |
| `deepseek-pair` | DeepSeek V4.1 Flash via OpenRouter, pinned to DeepSeek's own API, thinking off | one call per (query, passage); temperature 0, `max_tokens` 2, `top_logprobs` 10; score = P(yes) / (P(yes) + P(no)) over the first token |
| `deepseek-json` | same model | one call per query: all 30 passages, JSON with a 0–100 score per passage |
| `jev-noul-pair` | `jev-latest` | one call per (query, passage), one yes/no question; score = the probability (TypeSafe's reranking cookbook) |
| `jev-noul-batch` | `jev-latest` | one call per query: 30 passages in the state, 30 yes/no questions (their fan-out pattern) |
| `jev-choice` | `jev-latest` | one call per query: one Choice over the 30 passage ids plus `none`, and a yes/no "does any passage answer it?" (their semantic-search cookbook) |
| `jev-score-batch` | `jev-latest` | one call per query: 30 Score questions with a four-level rubric (off-topic / related / partly / fully); rank by the expected level |
| `jev-duel` | `jev-latest` | one call per query: BM25's top 10 in the state, all 45 pairwise Choices; rank by expected wins; 11–30 keep BM25 order |
| `jev-tournament` | `jev-latest` | two calls: six Choices over groups of five (+none), then a final Choice among the winners (+none) |
| `jev-cascade` | `jev-latest` | one batched yes/no call prunes 30 to 8, then per-pair yes/no on the 8 |
| `jev-choice-reversed` | `jev-latest` | `jev-choice` with the passages sent in reverse order (position-bias check only) |
| `qwen-rlcd-batch` / `qwen-rlcd-rubric` | Qwen2.5-1.5B-Instruct with parallel constrained decoding of JSON keys (the open-source "Qwen-2.5-1B-RLCD" recipe posted the day after Jev's launch; no training; transformers port `shreyansh26/Qwen-2.5-1B-RLCD`, Apache 2.0), self-hosted on rented RTX 4090s | one prefill per query, then all 30 keys scored in one batched pass with the model's own `run_parallel_generation`; 30 boolean keys with Jev's wording (score = P(true)) or 30 enum keys with Jev's 4-level rubric (score = expected level); when the one-shot pass runs out of memory on a 24 GB card (the longest code-heavy prompts in StackOverflow and robotics) the same keys are scored six at a time against the same prefill, and the raw row says so; `rlcd_runner.py` |
| `qwen-rlcd-pair` | same model and code | the fairest shape for a small model: one passage per prompt, one boolean key with Jev's wording, 30 prompts per query scored one after the other with the recipe's own function; score = P(true); latency = the sum of the 30 |
| `qwen-rlcd-batch-reversed` | same | `qwen-rlcd-batch` with the 30 passages in reverse order (order-sensitivity check, the twin of `jev-choice-reversed`); never in the rankings |

Jev, DeepSeek and the Qwen RLCD runs get the same wording: *"Does the passage contain the information needed to answer or verify the
query?"* (`rerankers/__init__.py`). Cohere and ZeroEntropy take the query and the documents.

## Fairness rules

- Same 30 candidates, same order, same 2,000-character truncation, same relevance wording for every model that takes one.
- Ties keep BM25 order for every model; `eval.py` also reports `ndcg10_ties_against`, `tied_top_share`, `zero_score_share`.
- The 8-dataset headline was fixed before the BRIGHT block and NevIR ran; they are reported separately, not averaged in.
- Public datasets may be in any model's training data. Stated, not fixable.
- Every test runs from Algeria, so every API gets the same network handicap.
- Every loss is shown. The raw responses are in `cache/`, one JSONL line per query, gzipped.

## Reproduce

```
uv sync
cp .env.example .env            # JEV_API_KEY, OPENROUTER_API_KEY, ZEROENTROPY_API_KEY
uv run candidates/build.py      # downloads the datasets, builds BM25 top-30 and the "absent" twins
uv run candidates/build_nevir.py
uv run run.py --model jev-score-batch --dataset all --workers 16
uv run run.py --model cohere-pro --dataset all --workers 12
uv run run.py --model zerank-2 --dataset all --workers 6
uv run eval.py                  # results/summary.md, results/summary.json, charts
uv run significance.py          # bootstrap ranges for every gap
uv run nevir_eval.py            # negation, paired accuracy
uv run rlcd_check.py            # signal and position drift of the Qwen RLCD scores
uv run network.py; uv run batching.py; uv run determinism.py; uv run coldstart.py 60 120 300 600 900
```

Runs resume: a query already in `cache/` (plain or `.gz`) is skipped, and a failed row is redone on the next run.
`--limit N` runs N uncached queries as a smoke test. To re-score without spending anything, skip the `run.py` lines:
the cache in this repo is complete. The whole benchmark cost about $61 in API calls.

## Layout

```
data/loaders.py        dataset download + one common shape
candidates/build.py    BM25 top-30 per query plus the "absent" twin  ->  candidates/<dataset>.jsonl (ids, queries, BM25 scores)
candidates/build_nevir.py
rerankers/             jev.py  cohere.py  zerank.py  llm_logprob.py  bm25.py
run.py                 one model on one dataset, both variants, caching every raw response
cache/<model>/         <dataset>.<variant>.jsonl.gz  one line per query: scores, every raw response, latency, usage, cost
eval.py                metrics, nothing-relevant test, calibration, charts  ->  results/
significance.py  nevir_eval.py  rlcd_check.py  network.py  batching.py  determinism.py  coldstart.py
rlcd_runner.py         the self-hosted Qwen RLCD recipe, run on a GPU pod, writing the same cache rows
blog.py                renders the write-up from results/*.json (numbers are never typed by hand)
```

`candidates/*.docs.jsonl` (the passage texts) are not committed for licensing reasons; `build.py` regenerates them
deterministically from the Hugging Face copies of the datasets.

## Public evidence viewer

The interactive evidence viewer lives in the personal website repository and
is available at [anessbelbati.com/lab/jev-reranking/](https://anessbelbati.com/lab/jev-reranking/).
This benchmark repository contains the experiments, saved results, and the data
exporter; it does not contain a separate website app.

With the local candidate passage files available, export the curated snapshot:

```powershell
uv run scripts/export_evidence.py
# Or write directly to a website checkout:
uv run scripts/export_evidence.py --output <website>/public/lab/jev-reranking/data
uv run -m unittest scripts/test_export_evidence.py
```

The default output is `exports/evidence/` (Git-ignored). The export contains
allowlisted saved outputs, the candidate snippets used in the run, prompt
templates, attribution, source hashes, and downloadable dataset archives.
Regeneration reads local records and makes no paid model calls.

## Prices used

| API | price | where it is stated | read |
|---|---|---|---|
| Jev | $0.042 per million input tokens, output free | typesafe.ai launch post | 2026-09-16 |
| Cohere Rerank 4 Pro | $2.50 per 1,000 searches (1 query + up to 100 docs); exact billed `usage.cost` per call from OpenRouter | OpenRouter response | 2026-09-16 |
| Cohere Rerank 4 Fast | $2.00 per 1,000 searches, same route | OpenRouter response | 2026-09-16 |
| ZeroEntropy zerank-2 | $0.025 per million tokens | zeroentropy.dev/pricing | 2026-09-16 |
| DeepSeek V4.1 Flash | $0.15 / $0.60 per million in / out; exact billed `usage.cost` per call from OpenRouter | OpenRouter response | 2026-09-16 |
| Qwen2.5-1.5B RLCD (self-hosted) | GPU seconds of each call × $0.74 per hour (RunPod secure-cloud RTX 4090 list price); pod setup time not included | runpod.io pricing | 2026-09-16 |

Usage totals per run (tokens, search units) are in `results/summary.md` so the cost can be checked against the vendor
dashboards.

## License

Code: MIT. The datasets keep their own licences (BEIR, MTEB/BRIGHT, CodeSearchNet, NevIR, MIRACL); only ids, queries
and scores are stored here.
