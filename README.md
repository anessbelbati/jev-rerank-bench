![Jev as a reranker. Equal-dataset nDCG@10: Jev rubric 0.692, Cohere Pro 0.691, ZeroEntropy zerank-2 0.682.](docs/readme-header.png)

# jev-rerank-bench

**The write-up:** [Jev vs Cohere Rerank 4 Pro vs zerank-2: reranker benchmark](https://anessbelbati.com/blog/i-gave-jev-a-rerankers-job) walks through the results, the negation test and the Qwen follow-up.

I gave [TypeSafe's Jev](https://typesafe.ai/blog/introducing-system-one-models-and-jev) thirty search results and asked
it which ones were useful. Then I gave Cohere and ZeroEntropy the same passages. This repository contains the experiments, saved responses and scoring code.

The ranking average put **Jev's rubric at 0.692 and Cohere Pro at 0.691**, without establishing a winner. Giving
every query equal weight instead puts Cohere ahead. Jev did better on the negation test than the rerankers; the open-weight Open-Jev 9B, run afterwards, reads negation better than Jev asked the same way (77% vs 71% of pairs). An open-source Qwen recipe
improved substantially when I gave it one passage at a time, but still showed no clear gain over keyword ranking.
Eight more open models, run September 25, all beat keyword ranking; the best of them, Qwen3-Reranker-4B, is within
noise of Jev asked one passage at a time (0.660 vs 0.670), trails Jev's rubric, and beats every Jev setup on French.

The main comparison covers eight English datasets. Five more BRIGHT subsets, NevIR negation pairs and MIRACL
French are reported separately. Models start with the same thirty BM25 candidates, cut to 2,000 characters each;
the duel variant only compares the first ten, and NevIR supplies its own two-passage pairs.

Measurements began September 16, 2026; the Qwen controls were added September 17. Jev calls used `jev-latest`,
reporting version 1.13.0. The [evidence viewer](https://anessbelbati.com/lab/jev-reranking/) includes the original
benchmark and the Qwen follow-up, with individual questions, scores and saved outputs.

Two follow-ups: [Does the order of the passages change Jev's pick?](https://anessbelbati.com/blog/does-passage-order-change-jevs-pick)
reverses, shuffles and renames the thirty passages, and
[prompt-injection-vs-keyword-stuffing-ai-seo](https://github.com/anessbelbati/prompt-injection-vs-keyword-stuffing-ai-seo)
adds one sentence to a wrong page and checks whether 13 rankers put it in their top five (100 searches).

## Headline (8 English datasets, 1,617 scored questions)

| Model | Runs on | nDCG@10, each dataset counts once | nDCG@10, each question counts once | Negation (NevIR pairs right) | Top pick right | Time per query | $ per 1,000 queries (self-hosted: GPU time) | Spots "nothing here" (AUROC) |
|---|---|---|---|---|---|---|---|---|
| Jev 4-level rubric, 30 in one call | API | 0.692 | 0.738 | 71% | 74% | 422 ms | 0.45 | 0.75 |
| Cohere Rerank 4 Pro | API | 0.691 | 0.756 | 67% | 73% | 844 ms | 2.51 | 0.78 |
| Jev 30 yes/no in one call | API | 0.685 | 0.737 | 70% | 72% | 396 ms | 0.41 | 0.75 |
| Jev one Choice + none | API | 0.684 | 0.733 | 66% | 76% | 338 ms | 0.33 | 0.72 |
| Cohere Rerank 4 Fast | API | 0.684 | 0.737 | — | 72% | 726 ms | 2.01 | 0.75 |
| ZeroEntropy zerank-2 | API | 0.682 | 0.729 | 61% | 72% | 1.8 s | 0.22 | 0.74 |
| DeepSeek V4.1 Flash JSON, 30 in one call | API | 0.682 | 0.721 | 22% | 73% | 2.2 s | 1.13 | 0.75 |
| Jev cascade (batch prune, then 8 pairs) | API | 0.674 | 0.722 | — | 69% | 2.5 s | 0.63 | 0.73 |
| Jev yes/no per pair | API | 0.670 | 0.717 | 71% | 70% | 8.2 s | 0.81 | 0.73 |
| Jev tournament (6 groups, then final) | API | 0.668 | 0.706 | — | 75% | 641 ms | 0.43 | 0.71 |
| DeepSeek V4.1 Flash P(yes) per pair | API | 0.608 | 0.663 | 17% | 62% | 34.3 s | 1.38 | 0.65 |
| Jev 45 duels in one call (top 10) | API | 0.580 | 0.635 | — | 66% | 324 ms | 0.21 | 0.65 |
| Qwen3-Reranker-4B | Self-hosted: RTX A5000 | 0.660 | 0.725 | 48% | 67% | 2.2 s | 0.18 | 0.75 |
| mxbai-rerank-base-v2 | Self-hosted: RTX A5000 | 0.642 | 0.716 | 38% | 66% | 1.2 s | 0.10 | 0.71 |
| tev1-4B relevant / not per pair | Self-hosted: RTX A5000 | 0.637 | 0.676 | 71% | 65% | 2.6 s | 0.20 | 0.71 |
| Winnow-12B Q8 yes/no per pair | Self-hosted: RTX A5000 | 0.634 | 0.685 | 73% | 63% | 12.8 s | 0.49 | 0.70 |
| Qwen3.5-4B yes/no per pair | Self-hosted: RTX A5000 | 0.628 | 0.670 | 62% | 63% | 2.3 s | 0.18 | 0.71 |
| reflex 4B yes/no per pair | Self-hosted: RTX A5000 | 0.622 | 0.666 | 61% | 60% | 10.1 s | 0.38 | 0.69 |
| Open-Jev 9B yes/no per pair | Self-hosted: A100, H100, L40S, RTX PRO 6000 | 0.600 | 0.642 | 77% | 59% | 19.1 s | 1.58 | 0.68 |
| bge-reranker-v2-m3 | Self-hosted: RTX A5000 | 0.588 | 0.676 | 43% | 58% | 896 ms | 0.07 | 0.67 |
| decider-2b v11 yes/no per pair | Self-hosted: RTX A5000 | 0.587 | 0.603 | 56% | 55% | 33.8 s | 0.08 | 0.67 |
| Open-Jev 2B yes/no per pair | Self-hosted: RTX 4090, L40S | 0.544 | 0.595 | 73% | 52% | 12.3 s | 0.31 | 0.65 |
| Laya 421M 4-level rubric per pair | Self-hosted: RTX 4090, RTX 3090, A40, L40S | 0.483 | 0.506 | 36% | 40% | 140 ms | 0.03 | 0.60 |
| Qwen2.5-1.5B RLCD, one passage per prompt | Self-hosted: RTX 4090 | 0.471 | 0.496 | 34% | 40% | 748 ms | 0.20 | 0.57 |
| Laya 421M yes/no per pair | Self-hosted: RTX 4090, RTX 3090, A40, L40S | 0.471 | 0.493 | 41% | 39% | 137 ms | 0.03 | 0.60 |
| GLiNER2.5 base 194M, relevant / not per pair | Self-hosted: RTX 4090, RTX 3090, A40, L40S | 0.419 | 0.443 | 44% | 35% | 293 ms | 0.07 | 0.57 |
| GLiNER2.5 multi 0.3B, relevant / not per pair | Self-hosted: RTX 4090, RTX 3090, A40, L40S | 0.416 | 0.430 | 31% | 35% | 469 ms | 0.11 | 0.57 |
| GLiNER2.5 small 74M, relevant / not per pair | Self-hosted: RTX 4090, RTX 3090, A40, L40S | 0.399 | 0.431 | 44% | 33% | 152 ms | 0.04 | 0.56 |
| Laya multilingual 322M yes/no per pair | Self-hosted: RTX 4090, RTX 3090, A40, L40S | 0.376 | 0.370 | 24% | 31% | 87 ms | 0.02 | 0.55 |
| Qwen2.5-1.5B RLCD, 30 rubric keys | Self-hosted: RTX 4090 | 0.340 | 0.339 | 19% | 30% | 419 ms | 0.09 | 0.55 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys | Self-hosted: RTX 4090 | 0.255 | 0.215 | 7% | 22% | 360 ms | 0.08 | 0.52 |
| BM25 (floor) | CPU | 0.486 | 0.525 | 2% | 45% | – | 0 | 0.58 |

**Self-hosted** rows ran on graphics cards rented from RunPod (secure cloud); "Runs on" names the cards. Their cost is
**GPU time, not an API price**: the seconds each call kept the card busy, times that card's hourly price, divided by
the number of requests the card was working on at once (model copies × requests in flight per copy). Setup and idle
time are left out. **Each dataset counts once** averages
the eight dataset scores (the headline figure); **each question counts once** averages all 1,617 questions, so FiQA's
411 count for more than BRIGHT's 39 and 38. A dash in the negation column means that setup was not run on NevIR.
Want another model here? [Test your own model](#test-your-own-model), or
[request one](https://github.com/anessbelbati/jev-rerank-bench/issues/new?template=request-a-model.yml).

- Ranking quality: Jev rubric minus Cohere Pro is +0.001, with a 95% interval of −0.009 to +0.012. This establishes
  neither a winner nor equivalence. With equal weight per query, Cohere scores **0.756** and Jev **0.738**.
- Top-ranked passage: Jev Choice leads Cohere Pro by 3.1 percentage points (95% interval +0.7 to +5.6). This metric
  ignores the separate `none` option; it is not the accuracy of the answer Jev actually selected.
- Negation (NevIR, 1,383 pairs): Jev rubric 71% of pairs right, Cohere Pro 67% (gap +4.2, range +1.5 to +6.9),
  ZeroEntropy 61%; the chat-model baseline 17–22%, below the 25% of guessing.
- Reasoning (7 BRIGHT subsets, 307 questions): Jev rubric averages 0.493 and DeepSeek JSON 0.487; their difference
  remains unresolved. These subjects are a separate comparison, not added to the eight-dataset headline.
- Qwen's one-passage control reaches 0.471, up from 0.255 with thirty yes/no fields. BM25 scores 0.486; the
  Qwen-minus-BM25 interval crosses zero. Details and attribution are below.
- Dataset differences: Cohere Pro leads Jev's yes/no batch by 5.0 points on FiQA, its rubric by 3.9 on Natural
  Questions, and its Choice setup by 6.4 on French. zerank-2 leads the rubric by 2.1 points on TREC-COVID.

The intervals are exploratory paired bootstraps, without adjustment for the multiple comparisons. NevIR kept
passage order fixed and reuses source passages across some pairs. Its 25% chance rate assumes independent random
choices for the two questions.

Table latency is the mean of dataset medians, not a pooled median. API calls include network and serving time;
self-hosted timings are model calls on rented GPUs. Costs average the eight dataset rates over all 2,327 original queries,
including queries without relevant candidates. API costs use saved usage and recorded rates; self-hosted costs cover
measured GPU time, excluding setup and idle time. These are not invoice-verified or equivalent deployment costs.

Full tables, per-dataset numbers, latency percentiles, usage totals and every check: `results/summary.md`,
`results/*.json`, and the charts in `results/`.

## The Qwen follow-up

[Harsha Gundala's original recipe](https://huggingface.co/harshatheg/Qwen-2.5-1B-RLCD) uses MLX on Apple Silicon.
I tested [Shreyansh Singh's Transformers/PyTorch port](https://huggingface.co/shreyansh26/Qwen-2.5-1B-RLCD) on rented
RTX 4090s. The base model is [Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct), from Alibaba's
Qwen team. Despite “1B” in the recipe's name, it is a 1.5-billion-parameter model. The port adds serving code and
presets, with no additional fine-tuning; it does not reproduce Jev's training or establish that their architectures match.

The tested `run_parallel_generation` processes the shared prompt once, then reuses its internal cache to evaluate
the fields in a batch. It scores the permitted labels and assembles JSON in code. Prefill and field evaluation
are separate model forwards, and some labels need continuation scoring. I did not test the port's separate tree
mode. Allowed types and normalized label scores do not guarantee correct judgments or calibrated confidence.

With thirty passages together, Qwen scored 0.255 using yes/no fields and 0.340 using the rubric, both below BM25's
0.486. Jev's rubric led Qwen's rubric by 35.2 points (95% interval +33.2 to +37.4). Giving Qwen one passage per prompt
raised it to **0.471**: +21.6 points over its thirty-passage yes/no setup, but no demonstrated improvement over BM25
(difference −0.015; 95% interval −0.033 to +0.004). NevIR paired accuracy was 7% for the batch yes/no configuration, 19% for
the rubric and 34% for the one-passage configuration.

Reversing the thirty passages changed Qwen's top-ranked passage on **1,498 of 1,617 queries (92.6%)**, compared with
**400 (24.7%)** for Jev Choice. As above, these are passage rankings, excluding Jev's `none` option. No repeated
identical Qwen requests were run. This measures order sensitivity, not repeatability or proof that position alone
determines the answer. The one-passage control also changes context length and prompt structure; it does not
isolate parallel decoding as the cause of the quality difference.

`rlcd_check.py` provides the score diagnostics: the relevant-minus-irrelevant yes/no score gap was 0.046 for Qwen
and 0.430 for Jev with the same wording; Qwen's mean score was 0.195 at slot 1 and 0.384 at slot 30. Under reversal,
mean absolute score changes were 0.160 for Qwen and 0.013 for Jev Choice. Those last two values use different score
scales—independent yes/no scores versus a distribution across choices—so they are not a relative stability measure.

This tests the port's ranking quality. It does not reproduce the original quantized Mac demo or test its advertised
JSON-generation speedup.

## What is measured

- **Ranking:** nDCG@10, Top-1, Recall@5 and MRR@10 over questions whose BM25 top-30 holds at least one labelled
  relevant passage. nDCG@10 rewards useful passages near the top; 0.69 does not mean 69% of questions answered
  correctly. It uses linear relevance gains and all supplied relevance labels for the ideal ranking. Ties keep
  BM25 order; the report also breaks ties against each model as a sensitivity check.
- **Latency:** client-observed API timings at the stated concurrency, plus Qwen model-call timings on rented GPUs.
  `network.py` records connection and server-header diagnostics; it does not isolate equivalent model-only times
  across providers. Cohere used OpenRouter, and ZeroEntropy served many calls in its slower fallback mode.
- **Cost:** saved usage multiplied by the recorded rates, or OpenRouter's returned `usage.cost`. These fields were
  not checked against invoices. The Qwen estimate covers measured GPU time only.
- **The "nothing relevant" test:** for every question, a twin list with every relevant passage removed and refilled
  from further down BM25. AUROC of the top score, and the false-accept rate at 90% recall. For Jev also its built-in
  `none` option and its "does any passage answer it?" question.
- **Calibration:** ECE and reliability curves for probability-like scores. Normalizing scores does not establish
  that their confidence values match observed error rates.
- **Uncertainty:** `significance.py` uses 10,000 paired bootstrap resamples of queries within each dataset, then
  averages across the fixed dataset set. An interval crossing zero is inconclusive, not evidence of equivalence.
- **Jev under the microscope:** TypeSafe's confidence bands against real answers, order sensitivity (same 30 passages
  reversed), repeated requests and cold start after 1–15 minutes idle. These repeat tests were on Jev, not Qwen.
- **Shared text:** `batching.py` records one request per batch size with the same thirty SciFact passages. Each
  query adds two typed questions and roughly 443 input tokens. Forty queries cost 2.7 times one query in those
  observations. Only the first query's choice was tracked; complete batched answers were not retained. This does
  not demonstrate quality across all forty answers or equivalent-quality savings over separate requests.
- **Negation:** `nevir_eval.py` scores NevIR by paired accuracy: both questions must rank their correct passage
  strictly higher; ties fail. Fixed passage order, repeated source passages and unadjusted comparisons limit inference.

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
MIRACL, over the 100-passage pool MTEB ships per query). Models share the candidate lists and 2,000-character
truncation; the duel's top-ten restriction and NevIR's two-passage pairs are listed separately. These are results
for this candidate-generation pipeline, not official full-benchmark scores. Truncation can remove relevant text,
and the source relevance labels may be incomplete.

## Models and how each is asked

| key | model | how |
|---|---|---|
| `bm25` | BM25 order | the floor; no API |
| `cohere-pro` / `cohere-fast` | Cohere `rerank-4-pro` / `rerank-4-fast` via OpenRouter's rerank endpoint (returned usage cost per call) | one call per query, 30 documents |
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
| `qwen-rlcd-batch` / `qwen-rlcd-rubric` | Qwen2.5-1.5B-Instruct; Shreyansh Singh's Transformers port of Harsha Gundala's constrained-decoding recipe, self-hosted on RTX 4090s | shared-prompt prefill followed by batched field evaluations using `run_parallel_generation`; boolean score = P(true), rubric score = expected level / 3. Some long code-heavy BRIGHT prompts used six fields at a time after GPU memory failures, recorded in the raw rows; see `rlcd_runner.py` |
| `qwen-rlcd-pair` | same model and code | one passage per prompt and one boolean key with the same relevance wording; thirty sequential prompts per query using the same inference function; score = P(true), query latency includes all thirty |
| `laya-noul-pair` / `laya-score-pair` / `laya-multi-noul-pair` | Laya 421M (English) and Laya multilingual 322M, `convaiinnovations/laya`, Apache 2.0, self-hosted on rented GPUs (RTX 4090 for 71% of calls; RTX 3090, A40, L40S for the rest) | one passage per prompt (512-token window), Jev's yes/no wording (score = P(true)) or Jev's 4-level rubric (score = expected level); `small_models_runner.py` |
| `gliner25-small-pair` / `gliner25-base-pair` / `gliner25-multi-pair` | Fastino GLiNER2.5 small 74M / base 194M / multi 0.3B, self-hosted on the same rented GPUs as Laya | one passage per prompt, labels `relevant` / `not relevant`; a span and label matcher used outside its design, listed for completeness |
| `open-jev-2b-noul-pair` / `open-jev-9b-noul-pair` | Open-Jev 2B / 9B (`ZefanCai/Open-Jev-2B`, `Open-Jev-9B`; LoRA + scalar head on Qwen3.5), self-hosted on rented GPUs | the `jev-noul-pair` shape, byte for byte, sent to a local Open-Jev server (`JEV_URL`, `JEV_MODEL=open-jev`); score = P(true); `run.py --cache-as` |
| `qwen3-reranker-4b` / `bge-reranker-v2-m3` / `mxbai-rerank-base-v2` | Qwen3-Reranker-4B (`Qwen/Qwen3-Reranker-4B`, rev 22e6836), BAAI bge-reranker-v2-m3 (rev 953dc6f) and mixedbread mxbai-rerank-base-v2 (rev 3ea9d4d), self-hosted on an RTX A5000 | one passage per prompt, each through its model card's own recipe (`inject/hf_runner.py`): Qwen3 the card's transformers prompt with its default web-search instruction, bf16, 8,192 tokens, score = logit(yes) − logit(no); bge the card's cross-encoder in float32 over the model's whole 8,192-token window (the card's example stops at 512), score = its one logit; mxbai the card's Sentence Transformers recipe (5.4.0 CrossEncoder with the repo's chat template and yes/no head, float32, 8,192 tokens), score = logit("1") − logit("0") |
| `qwen35-4b-yesno-pair` | Qwen3.5-4B as released (`Qwen/Qwen3.5-4B`, rev 851bf6e), thinking off, self-hosted on an RTX A5000 | one passage per prompt with the yes/no wording `deepseek-pair` got; score = P(yes) / (P(yes) + P(no)) on the first answer token |
| `tev1-4b-pair` | Together's Tev1-4B-experimental (`togethercomputer/Tev1-4B-experimental`, rev 0b7becf), self-hosted on an RTX A5000 | one passage per prompt in Tev1's own decision format (`examples/decide.py` of github.com/togethercomputer/tev1: its system instruction, the task as one JSON message of state, question and lettered options, thinking off); option A = the "relevant" wording Jev got, B = the "not relevant" wording; score = P(A) / (P(A) + P(B)) |
| `reflex-4b-noul-pair` / `winnow-12b-noul-pair` / `decider-2b-noul-pair` | three community rebuilds that answer System One: reflex 4B (github.com/kshetrajna12/reflex, tag `stable` = commit 19586a1: frozen Qwen3.5-4B, rev 851bf6e, read through reflex's prompt, each question in two option orders), Winnow-12B Q8 (`EldanRing/Winnow-12B`, Q8_0 GGUF from rev b2b1421, a merged LoRA fine-tune of Gemma 4 12B, on EldanRing/winnow-inference commit 77d1458, a modified llama.cpp) and decider-2b v11 (`Mapika/decider-2b`, rev 533964d, a fine-tune of Qwen3.5-2B-Base, through its own `decider/serve.py`), each self-hosted on an RTX A5000 | the `jev-noul-pair` request, sent to each project's own server through `rerankers/systemone.py` and its `models.yaml` entry; score = the returned probability of true |
| `qwen-rlcd-batch-reversed` | same | `qwen-rlcd-batch` with the 30 passages in reverse order (order-sensitivity check, the twin of `jev-choice-reversed`); never in the rankings |

The yes/no variants of Jev, DeepSeek and Qwen get the same wording: *"Does the passage contain the information needed to answer or verify the
query?"* (`rerankers/__init__.py`). Cohere and ZeroEntropy take the query and the documents.

## Open weights, self-hosted: Laya, GLiNER2.5 and Open-Jev (runs 2026-09-19 and 2026-09-22, their own block)

Laya (Convai Innovations, 421M, Apache 2.0) is the open-weight model with Jev's question shape: Choice, Score and yes/no answered with
probabilities. Its window is 512 tokens, so it ran one passage per prompt (the only shape it allows), with Jev's 4-level rubric and with Jev's
yes/no wording, on rented GPUs (mostly RTX 4090s; also RTX 3090, A40 and L40S); the like-for-like Jev row is "Jev yes/no per pair" (0.670). The three GLiNER2.5 models are span and label
matchers, not built for this, listed for completeness. Rows copied from the render; never averaged into the headline.

| Open weights, self-hosted (one passage per prompt) | nDCG@10 | worst-case ties | Top pick right | Time per list of 30 | $ per 1,000 |
|---|---|---|---|---|---|
| Laya 421M 4-level rubric per pair (self-hosted) | 0.483 | 0.474 | 40% | 140 ms | 0.03 |
| Laya 421M yes/no per pair (self-hosted) | 0.471 | 0.463 | 39% | 137 ms | 0.03 |
| Laya multilingual 322M yes/no per pair (self-hosted) | 0.376 | 0.372 | 31% | 87 ms | 0.02 |
| Open-Jev 2B yes/no per pair (self-hosted) | 0.544 | 0.544 | 52% | 12.3 s | 0.31 |
| Open-Jev 9B yes/no per pair (self-hosted) | 0.600 | 0.601 | 59% | 19.1 s | 1.58 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | 0.419 | 0.417 | 35% | 293 ms | 0.07 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | 0.416 | 0.416 | 35% | 469 ms | 0.11 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | 0.399 | 0.399 | 33% | 152 ms | 0.04 |
| BM25 (floor) | 0.486 | 0.487 | 45% | 0 ms | 0.00 |

- Laya rubric vs BM25: gap -0.3 points, range -2.3 to +1.6, within noise. NevIR pairs right: 36% (Jev rubric 71%).
- Laya's 512-token window cut 0.3% of passages on Natural Questions and 88.9% on BRIGHT StackOverflow (the cut counts are in
  `results/small_models_headline.txt`).
- GLiNER2.5 multi could not process 1 of 7,896 lists on a 24 GB card (a 19,341-character question); it is stored as failed, not scored.
  GLiNER ran out of GPU memory on 139 code-heavy lists at 30 passages per batch; they were redone in batches of 6 or 1 (same scores, slower).
- torch 2.4's fused attention gave NaN scores for Laya on mixed-length batches; fixed by zeroing NaNs at padded positions after each layer;
  batched scores match the library's own predict() within 0.004 (English) and 0.012 (multilingual). Libraries: laya 0.3.3, gliner2 2.0.0.
- Runner: `small_models_runner.py` (same cache rows as `run.py`, GPU seconds × the pod's hourly price).

Open-Jev (Zefan Cai, github.com/Zefan-Cai/Open-Jev; MIT code, Apache 2.0 adapters) is a LoRA adapter plus a scalar head on Qwen3.5-2B and
Qwen3.5-9B trained to answer the same three question types through the same request format as Jev. It ran through this repo's own Jev
request builders pointed at a local copy of its server (`JEV_URL`), one passage per prompt, Jev's exact yes/no wording and criteria, on rented
GPUs (2B: four server copies per card, on RTX 4090s for about 85% of calls and at the L40S price for the rest, going by the
hourly rate saved with each call; 9B: L40S, A100, H100, RTX PRO 6000, two to four copies per card). Run 2026-09-22.

- Open-Jev 2B vs BM25: gap +5.8 points, range +3.6 to +7.9, real.
- Open-Jev 9B vs BM25: gap +11.4 points, range +9.3 to +13.5, real.
- Jev yes/no per pair vs Open-Jev 9B, same shape: gap +7.0 points, 95% range +5.6 to +8.5, real. NevIR pairs right: 2B 73%, 9B 77% (Jev yes/no per pair 71%).
- Time and cost: GPU wall time of each call with several server copies sharing one card, so the per-list time carries contention and the
  dollar figure divides the pod price by the requests in flight on the card (copies × 2); both are rough. Corrected 2026-09-25: the first
  version divided by the copies only, which charged each second of card time twice ($3.16 and $0.63 per 1,000 queries); `openjev/fix_cost.py`
  halved the saved costs. RunPod's bill for the nine 9B pods that day, setup and idle time included, was $17.05, less than the $17.84 the
  first charge put on the calls alone. Passages longer than the servers' 4,096-token window (10 lists
  per size, all in BRIGHT robotics and StackOverflow) were redone on a 16,384-token server; every response is in `cache/open-jev-*`.
- Scripts: `openjev/pod.sh`, `openjev/fix.sh`, `openjev/merge.py`; the run's own tables: `results/eval_run_sept22.txt`,
  `results/significance_run_sept22.txt`.
- Setup: `pip install -e '.[train]'` of Open-Jev, adapters `ZefanCai/Open-Jev-2B` (rev 0c7aa49) and `Open-Jev-9B` (rev 47e9668),
  `python -m jev.server --checkpoint models/Open-Jev-<N>/package/checkpoint --max-length 4096`, then
  `JEV_URL=http://127.0.0.1:8791/v1/systemone JEV_MODEL=open-jev JEV_GPU_RATE=<pod $/h ÷ (copies × 2)> uv run run.py --model jev-noul-pair --cache-as open-jev-<n>-noul-pair --dataset all`.

## Open rerankers, two 4B models and three System One rebuilds, self-hosted (run 2026-09-25, their own block)

Three open rerankers, two small open models asked the yes/no question directly, and three community rebuilds of Jev that
answer TypeSafe's System One protocol, on five rented RTX A5000 cards (RunPod secure cloud, $0.27 an hour), one model at a
time per card, over all 14 datasets and NevIR, one passage per prompt. Their rows are in the main table.

- Every one of the eight beats BM25: from +10.1 points (decider-2b, range +8.3 to +12.0) to +17.4 (Qwen3-Reranker-4B,
  range +15.6 to +19.2), all real.
- Against Jev asked the same way (yes/no per pair, 0.670), Qwen3-Reranker-4B is within noise: Jev +1.0 points, range −0.2
  to +2.3. Jev leads the other seven by 2.8 points (mxbai-rerank-base-v2, range +1.3 to +4.4) to 8.3 (decider-2b, range
  +6.9 to +9.8), all real. Jev's rubric (0.692) leads all eight; Qwen3-Reranker-4B by 3.2 points, range +2.0 to +4.5.
- MIRACL French: Qwen3-Reranker-4B has the top score there, level with Cohere Rerank 4 Pro (0.766 vs 0.764), and leads
  Jev's best French setup (Choice) by 6.6 points, range +3.3 to +10.1, real.
- NevIR pairs right: Winnow-12B 73%, Tev1-4B 71% (Jev yes/no per pair 71%), Qwen3.5-4B 62%, reflex 61%, decider-2b 56%, the
  rerankers 48% (Qwen3), 43% (bge) and 38% (mxbai). Open-Jev 9B stays highest at 77%.
- reflex 4B is Qwen3.5-4B read through reflex's prompt, each question in two option orders; it scores 0.622, against 0.628
  for the same weights asked the plain yes/no question.
- The rerankers follow their model cards, pinned to exact revisions (`inject/hf_runner.py`). Before any benchmark question
  each scored its card's own printed example, and the run stopped unless the passages came out in the printed order with
  every score within 0.25 + 3% of the printed one: Qwen3-Reranker-4B gave 6.3125 and −14.3555 where its card prints 6.4375
  and −14.375 (bf16), bge −8.1838 and 5.265 where its card prints −8.1875 and 5.26171875, mxbai 9.7507, 1.3697, 8.0808,
  2.6612, 0.8730 and 0.3988 where its card prints 9.750735, 1.3697281, 8.080784, 2.6611633, 0.8729458 and 0.39884853.
- mixedbread's own `mxbai-rerank` library (0.1.0 to 0.1.6 alike) builds a shorter prompt than the card's Sentence
  Transformers recipe and scores the card's weaker passages up to 1.04 away from the printed numbers, so the card's recipe
  is the one run here. bge reads the model's whole 8,192-token window where the card's example stops at 512, so it sees
  the same text as every other model. The rerankers' scores are the logits their cards return by default: they order
  passages exactly as the probabilities do but never round to 1.0, so two confident passages do not tie.
- Qwen3.5-4B and Tev1-4B had only run in the prompt-injection test before. Both ran one prompt per forward pass: Qwen3.5
  mixes linear-attention layers with full attention, and one prompt per pass leaves no padding for those layers to read.
- The rebuilds answer the same `noul-pair` request Jev got, through `rerankers/systemone.py` and their `models.yaml`
  entries; their "30 passages in one request" setups were not run. reflex and Winnow answer one request at a time (two
  in flight, the second waits its turn); decider packs up to 32 into one forward pass, which is why its time per list is
  long and its cost low.
- Not run: SemIf (github.com/TheoLeeCJ/SemIf-OpenJev) has no server, only a command-line scorer with its own input
  format. djev (github.com/Davipar/djev-dev) takes the same request at `/v1/request`, not `/v1/systemone`; it needs an
  NVIDIA B200 (RunPod $6.79 an hour, none free on 2026-09-24), and its hosted service is paused.
- Time and cost: GPU wall time of each call; the dollar figure divides the card's $0.27 an hour by the requests in flight
  on it (1, 2 or 32, see Prices used). RunPod's bill for the whole step, setup, idle and a failed first attempt included:
  $10.07 (the five A5000 pods $9.71; four community-cloud pods and a test pod whose hosts' GPU drivers failed, $0.36).
- Scripts: `pods/hf.sh`, `pods/systemone.sh`, `inject/hf_runner.py`; the run's own tables: `results/eval_run_sept25.txt`,
  `results/significance_run_sept25.txt`.

## Fairness rules

- Same candidate lists and truncation, with the duel and NevIR exceptions documented above; shared wording for the yes/no variants.
- Ties keep BM25 order for every model; `eval.py` also reports `ndcg10_ties_against`, `tied_top_share`, `zero_score_share`.
- The 8-dataset headline was fixed before the BRIGHT block and NevIR ran; they are reported separately, not averaged in.
- Public datasets may be in any model's training data. Stated, not fixable.
- API clients ran from Algeria; providers and routing paths differed. Qwen ran on rented GPUs.
- Ranking responses are in `cache/`, one JSONL line per query, gzipped. Additional diagnostics save the fields listed in their scripts.

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
`--limit N` runs N uncached queries as a smoke test. To re-score saved results without model calls, run only
`eval.py`, `significance.py`, `nevir_eval.py` and `rlcd_check.py`. The `run.py`, network, batching, determinism and
cold-start commands above make new paid requests. Recorded API usage was about $61; that excludes GPU rental costs
and has not been reconciled against invoices.

## Test your own model

Any model served over TypeSafe's System One protocol can get a row in the main table, asked the way Jev was: the same
thirty passages, the same words, the same scoring. No server? [Request a model](https://github.com/anessbelbati/jev-rerank-bench/issues/new?template=request-a-model.yml).

**1. What your server must speak.** `POST <base_url>/systemone`, JSON in and out, with an optional
`Authorization: Bearer <key>` header. This is the whole request for one passage, the `noul-pair` setup:

```json
{
  "state": {
    "query": "what causes ocean tides",
    "passage": "Tides are caused mainly by the Moon's gravity pulling on the oceans."
  },
  "model": "your-model-id",
  "questions": {
    "relevant": {
      "type": "noul",
      "instructions": "Does the passage contain the information needed to answer or verify the query?",
      "criteria": {
        "true": "The passage states or directly implies the answer to the query, or the evidence that verifies it.",
        "false": "The passage is only on a related topic; it does not supply what the query asks for."
      }
    }
  }
}
```

A reply the benchmark reads: Jev's to a SciFact question, from `cache/jev-noul-pair/` (its `model` field left out). `noul` is
the probability of true:

```json
{"answers": {"relevant": {"type": "noul", "noul": 0.02}}, "usage": {"input_tokens": 594, "output_tokens": 22}}
```

The other setups send the same kind of request with more in it:

| Setup | `state` holds | Questions | Each answer must hold |
|---|---|---|---|
| `noul-pair` | `query`, `passage` | one `noul` (yes/no) | `noul`: the probability of true |
| `score-pair` | `query`, `passage` | one `score` with four criteria, off-topic to fully supplies | `probabilities` per level and a `legend` naming each level by the criterion text it was sent, or a `score` from 0 to 1 |
| `noul-batch`, `score-batch` | `query`, `passages` (`p01` to `p30`) | one per passage | as above |
| `choice`, `choice-reversed` | `query`, `passages` | a `choice` among the passage ids and `none`, and a `noul` "does any passage answer it?" | `probabilities` over the ids (plus `choice` and `confidence`), and `noul` |
| `tournament` | `query`, `passages` | six `choice` questions over groups of five (and `none`), then `choice` and `noul` on the six winners | as `choice` |
| `duel` | `query`, top 10 `passages` | 45 `choice` questions between two ids | `probabilities` over the two ids |
| `cascade` | both | `noul-batch`, then `noul-pair` on its top 8 | as above |

A server that holds one passage per request can still run `noul-pair` and `score-pair`. `usage` is optional: the
cost comes from GPU time on a self-hosted card, or from its token counts times your price. A reply the adapter
cannot read counts as a failed question, with the reason saved; it does not stop the run.

**2. Add an entry to `models.yaml`.** Its header explains every field: `base_url`, `model`, `modes` (the setups to
run), `max_context`, `passages_per_request`, `concurrency`, and optionally `key_env` (the name of the `.env` entry
with your key, never the key), `price`, `runs_on` and `label`. `uv run run.py --model <name> --plan` shows what will
run: a setup that needs more passages or tokens in one request than your server takes runs its one-passage form.

**3. Run it.** Once: `uv sync`, then `uv run candidates/build.py` and `uv run candidates/build_nevir.py` to rebuild the
passage texts, which are not in the repo; the committed lists in `candidates/*.jsonl` must come out unchanged
(`git status candidates/`). Then:

```
uv run bench.py <name> --smoke     # 20 questions per setup: does it answer, and how long and how much the full run takes
uv run bench.py <name>             # the full run: the 8 headline datasets (both lists) and NevIR, then your rows
```

A rerun skips every answered question and retries the failed ones. At the end `bench.py` packs
`cache/<name>-<mode>/` and prints your rows in the main table's format, scored with the same code
(`scripts/test_bench.py` checks that it reproduces every row already in the table).

**4. Open a pull request with your row.** On a branch of your fork, commit your entry in `models.yaml`, the saved
responses in `cache/<name>-<mode>/`, and your rows in the main table (API rows with the API group, self-hosted rows
with the self-hosted group, by score). In the description: a link to the weights or API and their license, the
server code and its commit, the card and its hourly price if self-hosted, and the date of the run. Before merging I
recompute every row from your saved responses with `uv run bench.py <name> --score`; a row that does not come out the
same waits.

## Layout

```
data/loaders.py        dataset download + one common shape
candidates/build.py    BM25 top-30 per query plus the "absent" twin  ->  candidates/<dataset>.jsonl (ids, queries, BM25 scores)
candidates/build_nevir.py
rerankers/             jev.py  cohere.py  zerank.py  llm_logprob.py  bm25.py
                       systemone.py (any System One server, asked Jev's eight ways), registry.py (reads models.yaml)
models.yaml            the System One models under test, one entry each (see "Test your own model")
run.py                 one model on one dataset, both variants, caching every raw response
bench.py               a models.yaml entry through the 8 headline datasets and NevIR, then its rows for the main table
cache/<model>/         <dataset>.<variant>.jsonl.gz  saved ranking responses, scores, latency, usage, cost
eval.py                metrics, nothing-relevant test, calibration, charts  ->  results/
significance.py  nevir_eval.py  rlcd_check.py  network.py  batching.py  determinism.py  coldstart.py
rlcd_runner.py         the self-hosted Qwen RLCD recipe, run on a GPU pod, writing the same cache rows
small_models_runner.py the self-hosted Laya / GLiNER2.5 runs (one passage per prompt), same cache rows
openjev/               pod.sh (one GPU pod: install Open-Jev, adapter, server copies, sharded run.py), fix.sh (full-window rerun
                       of the long lists), merge.py (merge the pod shards, verify coverage, write cache/), fix_cost.py (halve
                       the Sept 22 saved costs: two requests were in flight per server copy)
inject/hf_runner.py    open rerankers and small open models on a GPU pod (Qwen3-Reranker, bge, mxbai, Qwen3.5-4B, Tev1-4B),
                       one passage per prompt, writing the same cache rows
pods/                  hf.sh (one GPU pod for inject/hf_runner.py), systemone.sh (one GPU pod: a System One rebuild's own
                       server at its pinned version, then bench.py against it)
blog.py                renders an earlier experiment write-up from results/*.json
scripts/readme_header.py  draws the README header from saved scores and the website fonts
scripts/validate_systemone.py  replays the saved Jev responses behind the headline through systemone.py; --live asks real Jev
scripts/request_sizes.py  the largest request each setup sends  ->  results/request_sizes.json
scripts/test_registry.py  scripts/test_bench.py  tests for models.yaml and bench.py (no network)
.github/ISSUE_TEMPLATE/request-a-model.yml  the "Request a model" form
```

The full `candidates/*.docs.jsonl` passage files are not committed; `build.py` regenerates them from the datasets.
Saved model responses may quote source text, and the evidence exporter includes candidate snippets with attribution.

## Public evidence viewer

The interactive evidence viewer lives in the personal website repository and
is available at [anessbelbati.com/lab/jev-reranking/](https://anessbelbati.com/lab/jev-reranking/).
This benchmark repository contains the experiments, saved results, and the data
exporter; it does not contain a separate website app.
The viewer includes the Qwen batched yes/no, four-level rubric, one-passage and reversed-order runs.
The reversed-order run is an order-sensitivity diagnostic over the original eight datasets. Missing runs
remain marked as missing, including Qwen on MIRACL French. Qwen costs are GPU rental estimates and
its timings are measured on the GPU host; neither includes client network time or pod setup.
The source responses are also available in this repository's `cache/qwen-rlcd-*` directories.

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
| Cohere Rerank 4 Pro | $2.50 per 1,000 searches (1 query + up to 100 docs); reported `usage.cost` per call from OpenRouter | OpenRouter response | 2026-09-16 |
| Cohere Rerank 4 Fast | $2.00 per 1,000 searches, same route | OpenRouter response | 2026-09-16 |
| ZeroEntropy zerank-2 | $0.025 per million tokens | zeroentropy.dev/pricing | 2026-09-16 |
| DeepSeek V4.1 Flash | $0.15 / $0.60 per million in / out; reported `usage.cost` per call from OpenRouter | OpenRouter response | 2026-09-16 |
| Qwen2.5-1.5B RLCD (self-hosted) | GPU seconds of each call × $0.74 per hour (RunPod secure-cloud RTX 4090 list price); pod setup time not included | runpod.io pricing | 2026-09-16 |
| Laya, GLiNER2.5 (self-hosted) | GPU seconds of each call × the hourly price of the card it ran on, saved in each row (RunPod secure cloud: RTX 4090 $0.74, RTX 3090 $0.50, A40 $0.49, L40S $1.09); pod setup time not included | runpod.io pricing | 2026-09-19 |
| Open-Jev 2B / 9B (self-hosted) | GPU seconds of each call × the pod's hourly price ÷ requests in flight on the card, server copies × 2 (corrected 2026-09-25; RunPod secure cloud: RTX 4090 $0.74, L40S $1.09, A100 80GB $1.59, H100 SXM $3.49, RTX PRO 6000 $2.09); pod setup time not included | runpod.io pricing | 2026-09-22 |
| Qwen3-Reranker-4B, bge-reranker-v2-m3, mxbai-rerank-base-v2, Qwen3.5-4B, Tev1-4B, reflex 4B, Winnow-12B, decider-2b (self-hosted) | GPU seconds of each call × $0.27 per hour (RunPod secure-cloud RTX A5000) ÷ requests in flight on the card: 1 for the rerankers, Qwen3.5-4B and Tev1-4B (one process per card), 2 for reflex and Winnow (their servers answer one request at a time; the second waits), 32 for decider (its server packs them into one forward pass); pod setup time not included | RunPod API | 2026-09-25 |

Usage totals per run (tokens, search units) are in `results/summary.md` so the cost can be checked against the vendor
dashboards.

## License

Code: MIT. Dataset content keeps its source licences (BEIR, MTEB/BRIGHT, CodeSearchNet, NevIR and MIRACL), including
text quoted in saved responses or included in evidence exports. The exporter records source attribution; the code
licence does not replace dataset licences.
