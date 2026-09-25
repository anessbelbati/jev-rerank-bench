# Results

Ranking numbers are over queries whose BM25 top-30 contains at least one relevant passage. Latency = one HTTP round trip from Algiers, all calls of both variants. Cost = the API's own usage field × list price (OpenRouter reports the exact billed amount), per 1,000 queries of 30 candidates.

## TL;DR, English (average over the English datasets each model ran on)

| Model | datasets | nDCG@10 | Top-1 | median ms/call | median ms/query | $ per 1k queries | nothing-relevant AUROC | false accept @90% | ECE |
|---|---|---|---|---|---|---|---|---|---|
| BM25 (floor) | 8 | 0.486 | 0.453 | — | 0 | 0.00 | 0.581 | 0.821 | — |
| Cohere Rerank 4 Pro | 8 | 0.691 | 0.726 | 818 | 844 | 2.51 | 0.779 | 0.509 | — |
| Cohere Rerank 4 Fast | 8 | 0.684 | 0.715 | 685 | 726 | 2.01 | 0.752 | 0.581 | — |
| ZeroEntropy zerank-2 | 8 | 0.682 | 0.719 | 1779 | 1844 | 0.22 | 0.736 | 0.595 | — |
| DeepSeek V4.1 Flash P(yes) per pair | 8 | 0.608 | 0.617 | 1111 | 34257 | 1.38 | 0.650 | 0.804 | 0.112 |
| DeepSeek V4.1 Flash JSON, 30 in one call | 8 | 0.682 | 0.729 | 2212 | 2212 | 1.13 | 0.750 | 0.650 | — |
| Jev yes/no per pair | 8 | 0.670 | 0.699 | 263 | 8193 | 0.81 | 0.731 | 0.611 | 0.097 |
| Jev 30 yes/no in one call | 8 | 0.685 | 0.719 | 394 | 396 | 0.41 | 0.747 | 0.599 | 0.098 |
| Jev one Choice + none | 8 | 0.684 | 0.757 | 337 | 338 | 0.33 | 0.718 | 0.614 | — |
| Jev 4-level rubric, 30 in one call | 8 | 0.692 | 0.741 | 421 | 422 | 0.45 | 0.754 | 0.563 | — |
| Jev 45 duels in one call (top 10) | 8 | 0.580 | 0.658 | 324 | 324 | 0.21 | 0.651 | 0.723 | — |
| Jev tournament (6 groups, then final) | 8 | 0.668 | 0.753 | 296 | 641 | 0.43 | 0.711 | 0.634 | — |
| Jev cascade (batch prune, then 8 pairs) | 8 | 0.674 | 0.695 | 268 | 2533 | 0.63 | 0.732 | 0.601 | — |
| Jev one Choice, passages reversed | 8 | 0.680 | 0.735 | 346 | 349 | 0.33 | — | — | — |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | 8 | 0.255 | 0.220 | 360 | 360 | 0.08 | 0.516 | 0.894 | 0.240 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | 8 | 0.340 | 0.296 | 419 | 419 | 0.09 | 0.545 | 0.873 | — |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | 8 | 0.471 | 0.400 | 748 | 748 | 0.20 | 0.574 | 0.844 | 0.184 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | 8 | 0.386 | 0.304 | 354 | 354 | 0.08 | — | — | — |
| Laya 421M yes/no per pair (self-hosted) | 8 | 0.471 | 0.393 | 137 | 137 | 0.03 | 0.596 | 0.794 | 0.280 |
| Laya 421M 4-level rubric per pair (self-hosted) | 8 | 0.483 | 0.402 | 140 | 140 | 0.03 | 0.604 | 0.797 | — |
| Laya multilingual 322M yes/no per pair (self-hosted) | 8 | 0.376 | 0.315 | 87 | 87 | 0.02 | 0.550 | 0.845 | 0.364 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | 8 | 0.399 | 0.333 | 152 | 152 | 0.04 | 0.560 | 0.863 | 0.299 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | 8 | 0.419 | 0.347 | 293 | 293 | 0.07 | 0.573 | 0.841 | 0.324 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | 8 | 0.416 | 0.354 | 469 | 469 | 0.11 | 0.566 | 0.839 | 0.206 |
| Open-Jev 2B yes/no per pair (self-hosted) | 8 | 0.544 | 0.517 | 408 | 12348 | 0.31 | 0.646 | 0.737 | 0.111 |
| Open-Jev 9B yes/no per pair (self-hosted) | 8 | 0.600 | 0.593 | 627 | 19101 | 1.58 | 0.677 | 0.672 | 0.102 |
| Qwen3-Reranker-4B (self-hosted) | 8 | 0.660 | 0.673 | 2232 | 2232 | 0.18 | 0.754 | 0.556 | — |
| bge-reranker-v2-m3 (self-hosted) | 8 | 0.588 | 0.581 | 896 | 896 | 0.07 | 0.668 | 0.735 | — |
| mxbai-rerank-base-v2 (self-hosted) | 8 | 0.642 | 0.656 | 1222 | 1222 | 0.10 | 0.707 | 0.674 | — |
| Qwen3.5-4B yes/no per pair (self-hosted) | 8 | 0.628 | 0.631 | 2255 | 2255 | 0.18 | 0.706 | 0.637 | 0.100 |
| tev1-4B relevant / not per pair (self-hosted) | 8 | 0.637 | 0.646 | 2607 | 2607 | 0.20 | 0.705 | 0.638 | 0.126 |
| reflex 4B yes/no per pair (self-hosted) | 8 | 0.622 | 0.600 | 337 | 10088 | 0.38 | 0.693 | 0.660 | 0.116 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | 8 | 0.634 | 0.635 | 425 | 12827 | 0.49 | 0.704 | 0.644 | 0.118 |
| decider-2b v11 yes/no per pair (self-hosted) | 8 | 0.587 | 0.553 | 1089 | 33813 | 0.08 | 0.667 | 0.712 | 0.219 |

## All datasets including French

| Model | datasets | nDCG@10 | Top-1 | median ms/call | median ms/query | $ per 1k queries | nothing-relevant AUROC | false accept @90% | ECE |
|---|---|---|---|---|---|---|---|---|---|
| BM25 (floor) | 14 | 0.378 | 0.331 | — | 0 | 0.00 | 0.551 | 0.853 | — |
| Cohere Rerank 4 Pro | 14 | 0.619 | 0.662 | 885 | 998 | 2.55 | 0.732 | 0.588 | — |
| Cohere Rerank 4 Fast | 14 | 0.605 | 0.640 | 669 | 713 | 2.04 | 0.707 | 0.631 | — |
| ZeroEntropy zerank-2 | 14 | 0.617 | 0.666 | 1805 | 1884 | 0.24 | 0.702 | 0.659 | — |
| DeepSeek V4.1 Flash P(yes) per pair | 14 | 0.507 | 0.506 | 1093 | 33740 | 1.41 | 0.622 | 0.876 | 0.109 |
| DeepSeek V4.1 Flash JSON, 30 in one call | 14 | 0.612 | 0.679 | 2192 | 2192 | 1.09 | 0.717 | 0.699 | — |
| Jev yes/no per pair | 14 | 0.600 | 0.646 | 264 | 8313 | 0.88 | 0.704 | 0.652 | 0.079 |
| Jev 30 yes/no in one call | 14 | 0.616 | 0.652 | 435 | 455 | 0.40 | 0.717 | 0.637 | 0.086 |
| Jev one Choice + none | 14 | 0.606 | 0.687 | 382 | 394 | 0.32 | 0.696 | 0.639 | — |
| Jev 4-level rubric, 30 in one call | 14 | 0.623 | 0.683 | 467 | 519 | 0.43 | 0.724 | 0.605 | — |
| Jev 45 duels in one call (top 10) | 14 | 0.478 | 0.565 | 315 | 315 | 0.20 | 0.636 | 0.767 | — |
| Jev tournament (6 groups, then final) | 14 | 0.596 | 0.684 | 295 | 658 | 0.42 | 0.692 | 0.638 | — |
| Jev cascade (batch prune, then 8 pairs) | 14 | 0.606 | 0.642 | 270 | 2594 | 0.64 | 0.706 | 0.639 | — |
| Jev one Choice, passages reversed | 14 | 0.606 | 0.680 | 375 | 377 | 0.32 | 0.667 | 0.633 | — |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | 13 | 0.211 | 0.172 | 352 | 352 | 0.09 | 0.525 | 0.869 | 0.217 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | 13 | 0.267 | 0.224 | 409 | 409 | 0.10 | 0.543 | 0.864 | — |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | 13 | 0.385 | 0.311 | 805 | 805 | 0.20 | 0.554 | 0.861 | 0.175 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | 8 | 0.386 | 0.304 | 354 | 354 | 0.08 | — | — | — |
| Laya 421M yes/no per pair (self-hosted) | 14 | 0.397 | 0.304 | 140 | 140 | 0.03 | 0.565 | 0.826 | 0.313 |
| Laya 421M 4-level rubric per pair (self-hosted) | 14 | 0.398 | 0.312 | 141 | 141 | 0.03 | 0.573 | 0.823 | — |
| Laya multilingual 322M yes/no per pair (self-hosted) | 14 | 0.343 | 0.279 | 97 | 97 | 0.02 | 0.542 | 0.860 | 0.401 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | 14 | 0.320 | 0.245 | 181 | 181 | 0.05 | 0.540 | 0.877 | 0.330 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | 14 | 0.344 | 0.280 | 356 | 356 | 0.10 | 0.550 | 0.854 | 0.320 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | 14 | 0.357 | 0.296 | 569 | 569 | 0.15 | 0.550 | 0.850 | 0.220 |
| Open-Jev 2B yes/no per pair (self-hosted) | 14 | 0.453 | 0.423 | 419 | 12636 | 0.36 | 0.613 | 0.780 | 0.102 |
| Open-Jev 9B yes/no per pair (self-hosted) | 14 | 0.533 | 0.529 | 625 | 18951 | 1.75 | 0.650 | 0.723 | 0.085 |
| Qwen3-Reranker-4B (self-hosted) | 14 | 0.584 | 0.596 | 2462 | 2462 | 0.21 | 0.706 | 0.622 | — |
| bge-reranker-v2-m3 (self-hosted) | 14 | 0.502 | 0.481 | 1015 | 1015 | 0.09 | 0.630 | 0.771 | — |
| mxbai-rerank-base-v2 (self-hosted) | 14 | 0.552 | 0.542 | 1338 | 1338 | 0.11 | 0.657 | 0.736 | — |
| Qwen3.5-4B yes/no per pair (self-hosted) | 14 | 0.555 | 0.567 | 2372 | 2372 | 0.20 | 0.678 | 0.697 | 0.089 |
| tev1-4B relevant / not per pair (self-hosted) | 14 | 0.562 | 0.576 | 2749 | 2749 | 0.23 | 0.671 | 0.700 | 0.115 |
| reflex 4B yes/no per pair (self-hosted) | 14 | 0.546 | 0.531 | 343 | 10212 | 0.40 | 0.666 | 0.716 | 0.092 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | 14 | 0.566 | 0.576 | 466 | 14101 | 0.57 | 0.678 | 0.686 | 0.108 |
| decider-2b v11 yes/no per pair (self-hosted) | 14 | 0.545 | 0.532 | 1252 | 38560 | 0.09 | 0.656 | 0.736 | 0.196 |

## scifact

300 queries; 264 have an answer in BM25's top 30 and are scored.

| Model | n | nDCG@10 | Top-1 | Recall@5 | MRR@10 | calls | median ms/call | p95 ms/call | median ms/query | $ per 1k queries | none-test AUROC | false accept @90% | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BM25 (floor) | 264 | 0.780 | 0.625 | 0.837 | 0.738 | 0 | — | — | 0 | 0.00 | 0.674 | 0.731 | — |
| Cohere Rerank 4 Pro | 264 | 0.886 | 0.777 | 0.970 | 0.859 | 564 | 889 | 1375 | 951 | 2.50 | 0.862 | 0.455 | 0.256* |
| Cohere Rerank 4 Fast | 264 | 0.868 | 0.758 | 0.939 | 0.840 | 564 | 709 | 1345 | 887 | 2.00 | 0.833 | 0.500 | 0.248* |
| ZeroEntropy zerank-2 | 264 | 0.880 | 0.780 | 0.958 | 0.857 | 564 | 2008 | 3066 | 2008 | 0.27 | 0.814 | 0.470 | 0.174* |
| DeepSeek V4.1 Flash P(yes) per pair | 264 | 0.797 | 0.652 | 0.859 | 0.758 | 16920 | 1162 | 1405 | 34810 | 1.71 | 0.676 | 1.000 | 0.030 |
| DeepSeek V4.1 Flash JSON, 30 in one call | 264 | 0.849 | 0.742 | 0.903 | 0.822 | 564 | 2446 | 3482 | 2446 | 1.53 | 0.800 | 1.000 | 0.034* |
| Jev yes/no per pair | 264 | 0.880 | 0.788 | 0.934 | 0.856 | 16920 | 254 | 302 | 7818 | 0.90 | 0.837 | 0.458 | 0.023 |
| Jev 30 yes/no in one call | 264 | 0.895 | 0.814 | 0.952 | 0.872 | 564 | 328 | 873 | 328 | 0.56 | 0.836 | 0.455 | 0.032 |
| Jev one Choice + none | 264 | 0.892 | 0.822 | 0.937 | 0.878 | 564 | 319 | 782 | 320 | 0.47 | 0.857 | 0.405 | 0.013* |
| Jev 4-level rubric, 30 in one call | 264 | 0.889 | 0.807 | 0.955 | 0.866 | 564 | 414 | 1048 | 414 | 0.59 | 0.838 | 0.470 | 0.144* |
| Jev 45 duels in one call (top 10) | 264 | 0.863 | 0.803 | 0.906 | 0.855 | 564 | 289 | 512 | 289 | 0.25 | 0.830 | 0.527 | — |
| Jev tournament (6 groups, then final) | 264 | 0.869 | 0.811 | 0.864 | 0.855 | 1128 | 293 | 675 | 581 | 0.60 | 0.854 | 0.462 | — |
| Jev cascade (batch prune, then 8 pairs) | 264 | 0.881 | 0.784 | 0.936 | 0.854 | 5076 | 267 | 356 | 2508 | 0.80 | 0.837 | 0.458 | — |
| Jev one Choice, passages reversed | 264 | 0.885 | 0.803 | 0.943 | 0.868 | 300 | 383 | 825 | 383 | 0.47 | — | — | 0.013* |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | 264 | 0.186 | 0.038 | 0.194 | 0.127 | 564 | 519 | 692 | 519 | 0.16 | 0.474 | 0.909 | 0.346 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | 264 | 0.358 | 0.186 | 0.409 | 0.296 | 564 | 581 | 765 | 581 | 0.13 | 0.557 | 0.833 | 0.464* |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | 264 | 0.681 | 0.500 | 0.774 | 0.627 | 564 | 760 | 1602 | 760 | 0.23 | 0.630 | 0.860 | 0.139 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | 264 | 0.530 | 0.322 | 0.636 | 0.460 | 300 | 510 | 700 | 510 | 0.13 | — | — | 0.340* |
| Laya 421M yes/no per pair (self-hosted) | 264 | 0.600 | 0.405 | 0.728 | 0.535 | 564 | 144 | 407 | 144 | 0.04 | 0.613 | 0.811 | 0.266 |
| Laya 421M 4-level rubric per pair (self-hosted) | 264 | 0.627 | 0.432 | 0.735 | 0.564 | 564 | 144 | 279 | 144 | 0.03 | 0.625 | 0.811 | 0.410* |
| Laya multilingual 322M yes/no per pair (self-hosted) | 264 | 0.389 | 0.174 | 0.474 | 0.312 | 564 | 82 | 183 | 82 | 0.02 | 0.537 | 0.879 | 0.394 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | 264 | 0.521 | 0.345 | 0.579 | 0.463 | 564 | 174 | 441 | 174 | 0.05 | 0.595 | 0.883 | 0.130 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | 264 | 0.488 | 0.318 | 0.536 | 0.426 | 564 | 304 | 527 | 304 | 0.07 | 0.604 | 0.814 | 0.144 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | 264 | 0.434 | 0.265 | 0.471 | 0.369 | 564 | 482 | 934 | 482 | 0.11 | 0.571 | 0.860 | 0.099 |
| Open-Jev 2B yes/no per pair (self-hosted) | 264 | 0.680 | 0.538 | 0.749 | 0.638 | 16920 | 431 | 479 | 13097 | 0.32 | 0.705 | 0.746 | 0.015 |
| Open-Jev 9B yes/no per pair (self-hosted) | 264 | 0.709 | 0.606 | 0.768 | 0.680 | 16920 | 917 | 1103 | 28312 | 1.83 | 0.715 | 0.769 | 0.023 |
| Qwen3-Reranker-4B (self-hosted) | 264 | 0.880 | 0.788 | 0.946 | 0.855 | 564 | 2420 | 3073 | 2420 | 0.19 | 0.815 | 0.538 | — |
| bge-reranker-v2-m3 (self-hosted) | 264 | 0.840 | 0.735 | 0.893 | 0.811 | 564 | 985 | 1118 | 985 | 0.08 | 0.781 | 0.674 | — |
| mxbai-rerank-base-v2 (self-hosted) | 264 | 0.874 | 0.784 | 0.929 | 0.851 | 564 | 1323 | 1683 | 1323 | 0.10 | 0.819 | 0.545 | — |
| Qwen3.5-4B yes/no per pair (self-hosted) | 264 | 0.846 | 0.727 | 0.914 | 0.814 | 564 | 2507 | 3021 | 2507 | 0.19 | 0.768 | 0.602 | 0.020 |
| tev1-4B relevant / not per pair (self-hosted) | 264 | 0.846 | 0.727 | 0.908 | 0.813 | 564 | 2956 | 3454 | 2956 | 0.23 | 0.781 | 0.610 | 0.025 |
| reflex 4B yes/no per pair (self-hosted) | 264 | 0.866 | 0.758 | 0.921 | 0.836 | 16920 | 343 | 392 | 10267 | 0.40 | 0.786 | 0.568 | 0.035 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | 264 | 0.853 | 0.739 | 0.922 | 0.823 | 16920 | 463 | 585 | 13922 | 0.53 | 0.803 | 0.564 | 0.025 |
| decider-2b v11 yes/no per pair (self-hosted) | 264 | 0.750 | 0.606 | 0.836 | 0.710 | 16920 | 1241 | 2000 | 38713 | 0.09 | 0.701 | 0.773 | 0.243 |

Jev Choice's own nothing-relevant signals (scifact):

| signal | AUROC | false accept @90% | median with answer | median without |
|---|---|---|---|---|
| max_score | 0.857 | 0.405 | 0.890 | 0.085 |
| 1-P(none) | 0.849 | 0.402 | 0.955 | 0.125 |
| P(any) | 0.834 | 0.485 | 0.870 | 0.130 |

TypeSafe's confidence bands on real data, Jev one Choice + none (scifact), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 25 | 0.480 | 0.480 |
| 0.5-0.9 | 106 | 0.755 | 0.349 |
| >=0.9 | 133 | 0.940 | 0.098 |

TypeSafe's confidence bands on real data, Jev tournament (6 groups, then final) (scifact), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 27 | 0.444 | 0.000 |
| 0.5-0.9 | 95 | 0.758 | 0.000 |
| >=0.9 | 142 | 0.915 | 0.000 |

Position bias (scifact): the same 30 passages sent in reverse order to Jev Choice. Same top pick 90% of the time (n=264); nDCG@10 0.892 normal vs 0.885 reversed; mean probability shift per passage 0.005; P(none) shift 0.044.

## fiqa

648 queries; 411 have an answer in BM25's top 30 and are scored.

| Model | n | nDCG@10 | Top-1 | Recall@5 | MRR@10 | calls | median ms/call | p95 ms/call | median ms/query | $ per 1k queries | none-test AUROC | false accept @90% | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BM25 (floor) | 411 | 0.396 | 0.363 | 0.387 | 0.485 | 0 | — | — | 0 | 0.00 | 0.566 | 0.861 | — |
| Cohere Rerank 4 Pro | 411 | 0.670 | 0.788 | 0.640 | 0.861 | 1059 | 760 | 1245 | 789 | 2.50 | 0.814 | 0.484 | 0.508* |
| Cohere Rerank 4 Fast | 411 | 0.634 | 0.727 | 0.603 | 0.807 | 1059 | 629 | 1222 | 713 | 2.00 | 0.751 | 0.601 | 0.434* |
| ZeroEntropy zerank-2 | 411 | 0.611 | 0.684 | 0.600 | 0.779 | 1059 | 1478 | 2478 | 1478 | 0.18 | 0.696 | 0.686 | 0.364* |
| DeepSeek V4.1 Flash P(yes) per pair | 411 | 0.568 | 0.589 | 0.564 | 0.712 | 31770 | 1115 | 1386 | 33875 | 1.25 | 0.635 | 0.662 | 0.124 |
| DeepSeek V4.1 Flash JSON, 30 in one call | 411 | 0.613 | 0.703 | 0.590 | 0.787 | 1059 | 2221 | 3383 | 2221 | 1.10 | 0.733 | 0.662 | 0.140* |
| Jev yes/no per pair | 411 | 0.600 | 0.659 | 0.601 | 0.767 | 31770 | 253 | 302 | 7775 | 0.72 | 0.697 | 0.637 | 0.184 |
| Jev 30 yes/no in one call | 411 | 0.620 | 0.689 | 0.599 | 0.786 | 1059 | 298 | 526 | 299 | 0.39 | 0.730 | 0.591 | 0.163 |
| Jev one Choice + none | 411 | 0.617 | 0.693 | 0.602 | 0.793 | 1059 | 287 | 504 | 287 | 0.31 | 0.705 | 0.693 | 0.021* |
| Jev 4-level rubric, 30 in one call | 411 | 0.616 | 0.667 | 0.608 | 0.779 | 1059 | 315 | 746 | 316 | 0.42 | 0.717 | 0.586 | 0.306* |
| Jev 45 duels in one call (top 10) | 411 | 0.497 | 0.599 | 0.482 | 0.664 | 1059 | 283 | 463 | 284 | 0.20 | 0.660 | 0.742 | — |
| Jev tournament (6 groups, then final) | 411 | 0.581 | 0.698 | 0.495 | 0.772 | 2118 | 280 | 465 | 562 | 0.41 | 0.708 | 0.696 | — |
| Jev cascade (batch prune, then 8 pairs) | 411 | 0.607 | 0.659 | 0.591 | 0.768 | 9531 | 265 | 348 | 2468 | 0.59 | 0.699 | 0.640 | — |
| Jev one Choice, passages reversed | 411 | 0.614 | 0.686 | 0.603 | 0.786 | 648 | 322 | 562 | 322 | 0.31 | — | — | 0.021* |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | 411 | 0.205 | 0.119 | 0.196 | 0.233 | 1059 | 337 | 435 | 337 | 0.07 | 0.504 | 0.920 | 0.133 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | 411 | 0.300 | 0.258 | 0.278 | 0.383 | 1059 | 410 | 517 | 410 | 0.09 | 0.531 | 0.864 | 0.300* |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | 411 | 0.292 | 0.180 | 0.301 | 0.325 | 1059 | 703 | 1541 | 703 | 0.19 | 0.538 | 0.886 | 0.160 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | 411 | 0.332 | 0.258 | 0.323 | 0.398 | 648 | 342 | 439 | 342 | 0.07 | — | — | 0.139* |
| Laya 421M yes/no per pair (self-hosted) | 411 | 0.389 | 0.292 | 0.417 | 0.455 | 1059 | 144 | 270 | 144 | 0.03 | 0.573 | 0.827 | 0.274 |
| Laya 421M 4-level rubric per pair (self-hosted) | 411 | 0.381 | 0.280 | 0.400 | 0.448 | 1059 | 144 | 274 | 144 | 0.03 | 0.579 | 0.827 | 0.424* |
| Laya multilingual 322M yes/no per pair (self-hosted) | 411 | 0.292 | 0.190 | 0.297 | 0.335 | 1059 | 76 | 166 | 76 | 0.02 | 0.529 | 0.883 | 0.339 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | 411 | 0.325 | 0.253 | 0.312 | 0.386 | 1059 | 140 | 220 | 140 | 0.03 | 0.540 | 0.878 | 0.214 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | 411 | 0.358 | 0.292 | 0.363 | 0.434 | 1059 | 273 | 470 | 273 | 0.06 | 0.558 | 0.864 | 0.179 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | 411 | 0.329 | 0.255 | 0.323 | 0.394 | 1059 | 414 | 748 | 414 | 0.09 | 0.543 | 0.876 | 0.102 |
| Open-Jev 2B yes/no per pair (self-hosted) | 411 | 0.464 | 0.440 | 0.458 | 0.568 | 31770 | 398 | 448 | 12068 | 0.30 | 0.614 | 0.800 | 0.127 |
| Open-Jev 9B yes/no per pair (self-hosted) | 411 | 0.537 | 0.543 | 0.538 | 0.673 | 31770 | 710 | 1137 | 23187 | 1.46 | 0.656 | 0.672 | 0.041 |
| Qwen3-Reranker-4B (self-hosted) | 411 | 0.613 | 0.655 | 0.605 | 0.766 | 1059 | 2208 | 2620 | 2208 | 0.17 | 0.751 | 0.601 | — |
| bge-reranker-v2-m3 (self-hosted) | 411 | 0.578 | 0.630 | 0.570 | 0.734 | 1059 | 849 | 947 | 849 | 0.06 | 0.686 | 0.725 | — |
| mxbai-rerank-base-v2 (self-hosted) | 411 | 0.593 | 0.635 | 0.583 | 0.743 | 1059 | 1199 | 1407 | 1199 | 0.09 | 0.698 | 0.710 | — |
| Qwen3.5-4B yes/no per pair (self-hosted) | 411 | 0.521 | 0.513 | 0.517 | 0.649 | 1059 | 2101 | 2364 | 2101 | 0.16 | 0.648 | 0.749 | 0.161 |
| tev1-4B relevant / not per pair (self-hosted) | 411 | 0.528 | 0.530 | 0.518 | 0.664 | 1059 | 2402 | 2721 | 2402 | 0.18 | 0.652 | 0.725 | 0.261 |
| reflex 4B yes/no per pair (self-hosted) | 411 | 0.505 | 0.474 | 0.516 | 0.624 | 31770 | 332 | 387 | 9953 | 0.37 | 0.640 | 0.742 | 0.199 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | 411 | 0.559 | 0.572 | 0.566 | 0.704 | 31770 | 375 | 526 | 11499 | 0.43 | 0.672 | 0.674 | 0.185 |
| decider-2b v11 yes/no per pair (self-hosted) | 411 | 0.414 | 0.343 | 0.424 | 0.499 | 31770 | 975 | 1501 | 29333 | 0.07 | 0.599 | 0.810 | 0.326 |

Jev Choice's own nothing-relevant signals (fiqa):

| signal | AUROC | false accept @90% | median with answer | median without |
|---|---|---|---|---|
| max_score | 0.705 | 0.693 | 0.700 | 0.490 |
| 1-P(none) | 0.734 | 0.616 | 0.990 | 0.930 |
| P(any) | 0.694 | 0.630 | 0.930 | 0.830 |

TypeSafe's confidence bands on real data, Jev one Choice + none (fiqa), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 109 | 0.349 | 0.110 |
| 0.5-0.9 | 185 | 0.719 | 0.016 |
| >=0.9 | 117 | 0.974 | 0.000 |

TypeSafe's confidence bands on real data, Jev tournament (6 groups, then final) (fiqa), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 96 | 0.427 | 0.000 |
| 0.5-0.9 | 169 | 0.663 | 0.000 |
| >=0.9 | 146 | 0.918 | 0.000 |

Position bias (fiqa): the same 30 passages sent in reverse order to Jev Choice. Same top pick 76% of the time (n=411); nDCG@10 0.617 normal vs 0.614 reversed; mean probability shift per passage 0.015; P(none) shift 0.018.

## nq

500 queries; 320 have an answer in BM25's top 30 and are scored.

| Model | n | nDCG@10 | Top-1 | Recall@5 | MRR@10 | calls | median ms/call | p95 ms/call | median ms/query | $ per 1k queries | none-test AUROC | false accept @90% | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BM25 (floor) | 320 | 0.447 | 0.247 | 0.555 | 0.396 | 0 | — | — | 0 | 0.00 | 0.526 | 0.887 | — |
| Cohere Rerank 4 Pro | 320 | 0.846 | 0.750 | 0.901 | 0.849 | 820 | 649 | 1146 | 672 | 2.50 | 0.759 | 0.572 | 0.408* |
| Cohere Rerank 4 Fast | 320 | 0.815 | 0.694 | 0.908 | 0.809 | 820 | 602 | 1251 | 605 | 2.00 | 0.715 | 0.609 | 0.327* |
| ZeroEntropy zerank-2 | 320 | 0.791 | 0.656 | 0.884 | 0.782 | 820 | 2077 | 3047 | 2102 | 0.10 | 0.651 | 0.713 | 0.249* |
| DeepSeek V4.1 Flash P(yes) per pair | 320 | 0.685 | 0.481 | 0.799 | 0.650 | 24600 | 1070 | 1649 | 33919 | 0.79 | 0.598 | 0.747 | 0.097 |
| DeepSeek V4.1 Flash JSON, 30 in one call | 320 | 0.783 | 0.681 | 0.860 | 0.786 | 820 | 1880 | 2751 | 1880 | 0.63 | 0.676 | 0.750 | 0.084* |
| Jev yes/no per pair | 320 | 0.763 | 0.597 | 0.878 | 0.740 | 24600 | 271 | 368 | 8442 | 0.59 | 0.665 | 0.691 | 0.139 |
| Jev 30 yes/no in one call | 320 | 0.804 | 0.659 | 0.896 | 0.793 | 820 | 304 | 557 | 305 | 0.26 | 0.679 | 0.672 | 0.129 |
| Jev one Choice + none | 320 | 0.803 | 0.694 | 0.872 | 0.807 | 820 | 281 | 470 | 281 | 0.18 | 0.647 | 0.747 | 0.013* |
| Jev 4-level rubric, 30 in one call | 320 | 0.807 | 0.672 | 0.903 | 0.796 | 820 | 315 | 693 | 316 | 0.30 | 0.681 | 0.659 | 0.278* |
| Jev 45 duels in one call (top 10) | 320 | 0.631 | 0.581 | 0.676 | 0.653 | 820 | 299 | 784 | 299 | 0.15 | 0.596 | 0.825 | — |
| Jev tournament (6 groups, then final) | 320 | 0.764 | 0.662 | 0.758 | 0.756 | 1640 | 280 | 463 | 581 | 0.25 | 0.657 | 0.741 | — |
| Jev cascade (batch prune, then 8 pairs) | 320 | 0.768 | 0.600 | 0.885 | 0.745 | 7380 | 268 | 363 | 2515 | 0.43 | 0.674 | 0.672 | — |
| Jev one Choice, passages reversed | 320 | 0.794 | 0.669 | 0.872 | 0.792 | 500 | 288 | 547 | 289 | 0.18 | — | — | 0.012* |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | 320 | 0.245 | 0.106 | 0.280 | 0.211 | 820 | 191 | 252 | 191 | 0.04 | 0.519 | 0.875 | 0.322 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | 320 | 0.319 | 0.163 | 0.371 | 0.279 | 820 | 245 | 313 | 245 | 0.06 | 0.539 | 0.872 | 0.333* |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | 320 | 0.572 | 0.338 | 0.697 | 0.516 | 820 | 690 | 1551 | 690 | 0.19 | 0.560 | 0.844 | 0.205 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | 320 | 0.433 | 0.200 | 0.502 | 0.364 | 500 | 196 | 254 | 196 | 0.04 | — | — | 0.339* |
| Laya 421M yes/no per pair (self-hosted) | 320 | 0.564 | 0.353 | 0.664 | 0.513 | 820 | 107 | 235 | 107 | 0.02 | 0.584 | 0.825 | 0.265 |
| Laya 421M 4-level rubric per pair (self-hosted) | 320 | 0.578 | 0.381 | 0.687 | 0.535 | 820 | 115 | 246 | 115 | 0.02 | 0.587 | 0.806 | 0.413* |
| Laya multilingual 322M yes/no per pair (self-hosted) | 320 | 0.524 | 0.331 | 0.632 | 0.476 | 820 | 47 | 132 | 47 | 0.01 | 0.581 | 0.841 | 0.285 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | 320 | 0.520 | 0.256 | 0.642 | 0.451 | 820 | 82 | 138 | 82 | 0.02 | 0.541 | 0.866 | 0.255 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | 320 | 0.551 | 0.331 | 0.633 | 0.497 | 820 | 157 | 290 | 157 | 0.03 | 0.562 | 0.856 | 0.285 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | 320 | 0.556 | 0.341 | 0.667 | 0.501 | 820 | 235 | 451 | 235 | 0.05 | 0.566 | 0.847 | 0.232 |
| Open-Jev 2B yes/no per pair (self-hosted) | 320 | 0.657 | 0.441 | 0.788 | 0.614 | 24600 | 376 | 417 | 11330 | 0.27 | 0.605 | 0.766 | 0.132 |
| Open-Jev 9B yes/no per pair (self-hosted) | 320 | 0.727 | 0.531 | 0.848 | 0.690 | 24600 | 494 | 941 | 14007 | 1.20 | 0.639 | 0.684 | 0.044 |
| Qwen3-Reranker-4B (self-hosted) | 320 | 0.788 | 0.644 | 0.869 | 0.774 | 820 | 1398 | 2140 | 1398 | 0.11 | 0.722 | 0.634 | — |
| bge-reranker-v2-m3 (self-hosted) | 320 | 0.801 | 0.681 | 0.872 | 0.794 | 820 | 497 | 851 | 497 | 0.04 | 0.676 | 0.734 | — |
| mxbai-rerank-base-v2 (self-hosted) | 320 | 0.797 | 0.669 | 0.893 | 0.787 | 820 | 775 | 1163 | 775 | 0.06 | 0.656 | 0.741 | — |
| Qwen3.5-4B yes/no per pair (self-hosted) | 320 | 0.711 | 0.525 | 0.802 | 0.676 | 820 | 1786 | 1939 | 1786 | 0.14 | 0.655 | 0.738 | 0.115 |
| tev1-4B relevant / not per pair (self-hosted) | 320 | 0.729 | 0.547 | 0.847 | 0.698 | 820 | 1928 | 2148 | 1928 | 0.15 | 0.642 | 0.753 | 0.155 |
| reflex 4B yes/no per pair (self-hosted) | 320 | 0.721 | 0.516 | 0.847 | 0.687 | 24600 | 323 | 382 | 9748 | 0.37 | 0.651 | 0.728 | 0.106 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | 320 | 0.737 | 0.562 | 0.865 | 0.709 | 24600 | 284 | 370 | 8751 | 0.33 | 0.668 | 0.719 | 0.124 |
| decider-2b v11 yes/no per pair (self-hosted) | 320 | 0.704 | 0.497 | 0.844 | 0.663 | 24600 | 692 | 1010 | 20868 | 0.05 | 0.628 | 0.803 | 0.233 |

Jev Choice's own nothing-relevant signals (nq):

| signal | AUROC | false accept @90% | median with answer | median without |
|---|---|---|---|---|
| max_score | 0.647 | 0.747 | 0.840 | 0.660 |
| 1-P(none) | 0.681 | 0.666 | 0.990 | 0.970 |
| P(any) | 0.670 | 0.678 | 0.965 | 0.920 |

TypeSafe's confidence bands on real data, Jev one Choice + none (nq), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 48 | 0.500 | 0.104 |
| 0.5-0.9 | 141 | 0.567 | 0.050 |
| >=0.9 | 131 | 0.901 | 0.000 |

TypeSafe's confidence bands on real data, Jev tournament (6 groups, then final) (nq), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 40 | 0.450 | 0.000 |
| 0.5-0.9 | 116 | 0.526 | 0.000 |
| >=0.9 | 164 | 0.811 | 0.000 |

Position bias (nq): the same 30 passages sent in reverse order to Jev Choice. Same top pick 68% of the time (n=320); nDCG@10 0.803 normal vs 0.794 reversed; mean probability shift per passage 0.017; P(none) shift 0.016.

## nfcorpus

323 queries; 239 have an answer in BM25's top 30 and are scored.

| Model | n | nDCG@10 | Top-1 | Recall@5 | MRR@10 | calls | median ms/call | p95 ms/call | median ms/query | $ per 1k queries | none-test AUROC | false accept @90% | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BM25 (floor) | 239 | 0.435 | 0.594 | 0.163 | 0.710 | 0 | — | — | 0 | 0.00 | 0.660 | 0.710 | — |
| Cohere Rerank 4 Pro | 239 | 0.499 | 0.695 | 0.191 | 0.796 | 561 | 941 | 1743 | 954 | 2.50 | 0.733 | 0.567 | 0.292* |
| Cohere Rerank 4 Fast | 239 | 0.496 | 0.720 | 0.193 | 0.802 | 561 | 728 | 1758 | 735 | 2.00 | 0.713 | 0.618 | 0.194* |
| ZeroEntropy zerank-2 | 239 | 0.506 | 0.699 | 0.195 | 0.800 | 561 | 2056 | 3132 | 2065 | 0.27 | 0.733 | 0.592 | 0.196* |
| DeepSeek V4.1 Flash P(yes) per pair | 239 | 0.463 | 0.661 | 0.171 | 0.761 | 16830 | 1065 | 1374 | 32719 | 1.72 | 0.653 | 1.000 | 0.170 |
| DeepSeek V4.1 Flash JSON, 30 in one call | 239 | 0.493 | 0.674 | 0.188 | 0.780 | 561 | 2455 | 3558 | 2455 | 1.59 | 0.741 | 0.592 | 0.098* |
| Jev yes/no per pair | 239 | 0.482 | 0.674 | 0.189 | 0.775 | 16830 | 265 | 356 | 8317 | 0.89 | 0.719 | 0.634 | 0.037 |
| Jev 30 yes/no in one call | 239 | 0.498 | 0.682 | 0.193 | 0.778 | 561 | 372 | 796 | 373 | 0.56 | 0.704 | 0.626 | 0.036 |
| Jev one Choice + none | 239 | 0.477 | 0.678 | 0.189 | 0.778 | 561 | 327 | 764 | 328 | 0.48 | 0.659 | 0.714 | 0.158* |
| Jev 4-level rubric, 30 in one call | 239 | 0.500 | 0.695 | 0.194 | 0.787 | 561 | 373 | 1098 | 374 | 0.60 | 0.726 | 0.626 | 0.094* |
| Jev 45 duels in one call (top 10) | 239 | 0.459 | 0.690 | 0.173 | 0.785 | 561 | 341 | 568 | 342 | 0.25 | 0.586 | 0.845 | — |
| Jev tournament (6 groups, then final) | 239 | 0.440 | 0.699 | 0.138 | 0.778 | 1122 | 310 | 681 | 624 | 0.61 | 0.665 | 0.681 | — |
| Jev cascade (batch prune, then 8 pairs) | 239 | 0.496 | 0.682 | 0.189 | 0.784 | 5049 | 273 | 394 | 2570 | 0.81 | 0.718 | 0.605 | — |
| Jev one Choice, passages reversed | 239 | 0.478 | 0.682 | 0.186 | 0.784 | 323 | 325 | 719 | 354 | 0.48 | — | — | 0.156* |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | 239 | 0.228 | 0.251 | 0.063 | 0.389 | 561 | 560 | 644 | 560 | 0.13 | 0.522 | 0.924 | 0.147 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | 239 | 0.282 | 0.381 | 0.091 | 0.509 | 561 | 621 | 708 | 621 | 0.14 | 0.525 | 0.933 | 0.312* |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | 239 | 0.360 | 0.452 | 0.129 | 0.587 | 561 | 750 | 1369 | 750 | 0.23 | 0.600 | 0.832 | 0.125 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | 239 | 0.298 | 0.326 | 0.089 | 0.468 | 323 | 547 | 632 | 547 | 0.11 | — | — | 0.138* |
| Laya 421M yes/no per pair (self-hosted) | 239 | 0.386 | 0.494 | 0.155 | 0.632 | 561 | 144 | 273 | 144 | 0.03 | 0.641 | 0.735 | 0.051 |
| Laya 421M 4-level rubric per pair (self-hosted) | 239 | 0.402 | 0.527 | 0.154 | 0.649 | 561 | 144 | 275 | 144 | 0.03 | 0.644 | 0.765 | 0.174* |
| Laya multilingual 322M yes/no per pair (self-hosted) | 239 | 0.337 | 0.414 | 0.116 | 0.555 | 561 | 81 | 169 | 81 | 0.02 | 0.584 | 0.836 | 0.093 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | 239 | 0.394 | 0.506 | 0.138 | 0.630 | 561 | 150 | 225 | 150 | 0.03 | 0.630 | 0.761 | 0.187 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | 239 | 0.307 | 0.310 | 0.094 | 0.477 | 561 | 288 | 478 | 288 | 0.06 | 0.561 | 0.853 | 0.306 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | 239 | 0.347 | 0.385 | 0.125 | 0.546 | 561 | 467 | 822 | 467 | 0.10 | 0.594 | 0.866 | 0.192 |
| Open-Jev 2B yes/no per pair (self-hosted) | 239 | 0.442 | 0.565 | 0.177 | 0.702 | 16830 | 429 | 475 | 13010 | 0.33 | 0.646 | 0.702 | 0.106 |
| Open-Jev 9B yes/no per pair (self-hosted) | 239 | 0.429 | 0.544 | 0.176 | 0.675 | 16830 | 647 | 1342 | 18813 | 1.70 | 0.652 | 0.668 | 0.147 |
| Qwen3-Reranker-4B (self-hosted) | 239 | 0.495 | 0.686 | 0.192 | 0.790 | 561 | 2434 | 2959 | 2434 | 0.19 | 0.723 | 0.613 | — |
| bge-reranker-v2-m3 (self-hosted) | 239 | 0.459 | 0.623 | 0.183 | 0.745 | 561 | 944 | 1050 | 944 | 0.07 | 0.693 | 0.681 | — |
| mxbai-rerank-base-v2 (self-hosted) | 239 | 0.487 | 0.703 | 0.192 | 0.798 | 561 | 1334 | 1606 | 1334 | 0.10 | 0.722 | 0.655 | — |
| Qwen3.5-4B yes/no per pair (self-hosted) | 239 | 0.443 | 0.573 | 0.182 | 0.702 | 561 | 2586 | 2829 | 2586 | 0.19 | 0.655 | 0.676 | 0.111 |
| tev1-4B relevant / not per pair (self-hosted) | 239 | 0.457 | 0.615 | 0.180 | 0.722 | 561 | 3012 | 3238 | 3012 | 0.22 | 0.686 | 0.634 | 0.143 |
| reflex 4B yes/no per pair (self-hosted) | 239 | 0.446 | 0.615 | 0.178 | 0.718 | 16830 | 337 | 387 | 10156 | 0.37 | 0.682 | 0.681 | 0.116 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | 239 | 0.445 | 0.598 | 0.183 | 0.711 | 16830 | 473 | 573 | 14215 | 0.53 | 0.671 | 0.626 | 0.159 |
| decider-2b v11 yes/no per pair (self-hosted) | 239 | 0.328 | 0.351 | 0.120 | 0.516 | 16830 | 1247 | 2047 | 38480 | 0.09 | 0.557 | 0.853 | 0.294 |

Jev Choice's own nothing-relevant signals (nfcorpus):

| signal | AUROC | false accept @90% | median with answer | median without |
|---|---|---|---|---|
| max_score | 0.659 | 0.714 | 0.505 | 0.300 |
| 1-P(none) | 0.689 | 0.693 | 0.820 | 0.630 |
| P(any) | 0.707 | 0.639 | 0.660 | 0.520 |

TypeSafe's confidence bands on real data, Jev one Choice + none (nfcorpus), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 95 | 0.611 | 0.358 |
| 0.5-0.9 | 116 | 0.681 | 0.259 |
| >=0.9 | 28 | 0.893 | 0.071 |

TypeSafe's confidence bands on real data, Jev tournament (6 groups, then final) (nfcorpus), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 75 | 0.547 | 0.000 |
| 0.5-0.9 | 107 | 0.720 | 0.000 |
| >=0.9 | 57 | 0.860 | 0.000 |

Position bias (nfcorpus): the same 30 passages sent in reverse order to Jev Choice. Same top pick 50% of the time (n=239); nDCG@10 0.477 normal vs 0.478 reversed; mean probability shift per passage 0.018; P(none) shift 0.052.

## trec-covid

50 queries; 50 have an answer in BM25's top 30 and are scored.

| Model | n | nDCG@10 | Top-1 | Recall@5 | MRR@10 | calls | median ms/call | p95 ms/call | median ms/query | $ per 1k queries | none-test AUROC | false accept @90% | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BM25 (floor) | 50 | 0.621 | 0.800 | 0.009 | 0.876 | 0 | — | — | 0 | 0.00 | 0.622 | 0.767 | — |
| Cohere Rerank 4 Pro | 50 | 0.792 | 0.960 | 0.012 | 0.971 | 93 | 862 | 2051 | 862 | 2.50 | 0.840 | 0.442 | 0.168* |
| Cohere Rerank 4 Fast | 50 | 0.799 | 0.960 | 0.012 | 0.973 | 93 | 700 | 1587 | 701 | 2.00 | 0.827 | 0.581 | 0.103* |
| ZeroEntropy zerank-2 | 50 | 0.800 | 0.960 | 0.012 | 0.980 | 93 | 2843 | 3298 | 3012 | 0.21 | 0.844 | 0.535 | 0.051* |
| DeepSeek V4.1 Flash P(yes) per pair | 50 | 0.733 | 0.920 | 0.011 | 0.953 | 2790 | 1065 | 1382 | 32786 | 1.36 | 0.651 | 0.651 | 0.271 |
| DeepSeek V4.1 Flash JSON, 30 in one call | 50 | 0.800 | 0.960 | 0.012 | 0.973 | 93 | 2473 | 3388 | 2474 | 1.20 | 0.827 | 0.558 | 0.141* |
| Jev yes/no per pair | 50 | 0.764 | 0.920 | 0.011 | 0.947 | 2790 | 263 | 347 | 8258 | 0.78 | 0.769 | 0.744 | 0.249 |
| Jev 30 yes/no in one call | 50 | 0.775 | 0.940 | 0.012 | 0.958 | 93 | 687 | 1651 | 688 | 0.44 | 0.819 | 0.698 | 0.246 |
| Jev one Choice + none | 50 | 0.750 | 0.960 | 0.011 | 0.973 | 93 | 537 | 1499 | 537 | 0.36 | 0.698 | 0.721 | 0.547* |
| Jev 4-level rubric, 30 in one call | 50 | 0.779 | 0.940 | 0.012 | 0.959 | 93 | 706 | 1710 | 707 | 0.48 | 0.819 | 0.535 | 0.154* |
| Jev 45 duels in one call (top 10) | 50 | 0.652 | 0.920 | 0.010 | 0.942 | 93 | 461 | 1222 | 462 | 0.21 | 0.630 | 0.860 | — |
| Jev tournament (6 groups, then final) | 50 | 0.747 | 0.920 | 0.011 | 0.957 | 186 | 311 | 1325 | 836 | 0.47 | 0.595 | 0.837 | — |
| Jev cascade (batch prune, then 8 pairs) | 50 | 0.770 | 0.920 | 0.011 | 0.948 | 837 | 275 | 510 | 2711 | 0.67 | 0.769 | 0.698 | — |
| Jev one Choice, passages reversed | 50 | 0.741 | 0.940 | 0.011 | 0.964 | 50 | 477 | 1486 | 477 | 0.36 | — | — | 0.547* |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | 50 | 0.650 | 0.840 | 0.010 | 0.903 | 93 | 395 | 525 | 395 | 0.08 | 0.529 | 0.977 | 0.237 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | 50 | 0.609 | 0.820 | 0.010 | 0.895 | 93 | 453 | 591 | 453 | 0.10 | 0.697 | 0.721 | 0.124* |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | 50 | 0.707 | 0.880 | 0.011 | 0.919 | 93 | 722 | 1329 | 722 | 0.18 | 0.646 | 0.698 | 0.260 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | 50 | 0.657 | 0.840 | 0.010 | 0.904 | 50 | 386 | 532 | 386 | 0.08 | — | — | 0.243* |
| Laya 421M yes/no per pair (self-hosted) | 50 | 0.693 | 0.860 | 0.011 | 0.916 | 93 | 143 | 270 | 143 | 0.03 | 0.725 | 0.605 | 0.077 |
| Laya 421M 4-level rubric per pair (self-hosted) | 50 | 0.699 | 0.820 | 0.011 | 0.896 | 93 | 143 | 273 | 143 | 0.03 | 0.756 | 0.674 | 0.068* |
| Laya multilingual 322M yes/no per pair (self-hosted) | 50 | 0.654 | 0.800 | 0.010 | 0.883 | 93 | 71 | 143 | 71 | 0.02 | 0.585 | 0.744 | 0.123 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | 50 | 0.650 | 0.800 | 0.010 | 0.876 | 93 | 134 | 201 | 134 | 0.03 | 0.601 | 0.860 | 0.327 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | 50 | 0.697 | 0.780 | 0.010 | 0.865 | 93 | 261 | 441 | 261 | 0.05 | 0.673 | 0.698 | 0.279 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | 50 | 0.671 | 0.800 | 0.010 | 0.886 | 93 | 404 | 705 | 404 | 0.08 | 0.665 | 0.651 | 0.278 |
| Open-Jev 2B yes/no per pair (self-hosted) | 50 | 0.699 | 0.860 | 0.010 | 0.904 | 2790 | 385 | 448 | 11701 | 0.26 | 0.733 | 0.581 | 0.234 |
| Open-Jev 9B yes/no per pair (self-hosted) | 50 | 0.723 | 0.900 | 0.011 | 0.938 | 2790 | 513 | 1260 | 15255 | 1.43 | 0.719 | 0.581 | 0.413 |
| Qwen3-Reranker-4B (self-hosted) | 50 | 0.790 | 0.920 | 0.012 | 0.952 | 93 | 2204 | 2663 | 2204 | 0.17 | 0.885 | 0.372 | — |
| bge-reranker-v2-m3 (self-hosted) | 50 | 0.749 | 0.900 | 0.011 | 0.934 | 93 | 866 | 979 | 866 | 0.06 | 0.745 | 0.628 | — |
| mxbai-rerank-base-v2 (self-hosted) | 50 | 0.741 | 0.860 | 0.011 | 0.916 | 93 | 1220 | 1489 | 1220 | 0.09 | 0.762 | 0.581 | — |
| Qwen3.5-4B yes/no per pair (self-hosted) | 50 | 0.725 | 0.900 | 0.011 | 0.934 | 93 | 2179 | 2519 | 2179 | 0.17 | 0.763 | 0.605 | 0.248 |
| tev1-4B relevant / not per pair (self-hosted) | 50 | 0.756 | 0.900 | 0.011 | 0.945 | 93 | 2537 | 2944 | 2537 | 0.19 | 0.812 | 0.419 | 0.157 |
| reflex 4B yes/no per pair (self-hosted) | 50 | 0.739 | 0.860 | 0.011 | 0.917 | 2790 | 334 | 389 | 10043 | 0.38 | 0.749 | 0.651 | 0.258 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | 50 | 0.739 | 0.900 | 0.011 | 0.943 | 2790 | 400 | 514 | 12024 | 0.46 | 0.749 | 0.605 | 0.256 |
| decider-2b v11 yes/no per pair (self-hosted) | 50 | 0.713 | 0.820 | 0.011 | 0.900 | 2790 | 912 | 1651 | 30943 | 0.07 | 0.742 | 0.535 | 0.145 |

Jev Choice's own nothing-relevant signals (trec-covid):

| signal | AUROC | false accept @90% | median with answer | median without |
|---|---|---|---|---|
| max_score | 0.698 | 0.721 | 0.530 | 0.400 |
| 1-P(none) | 0.790 | 0.651 | 0.990 | 0.880 |
| P(any) | 0.822 | 0.581 | 0.950 | 0.790 |

TypeSafe's confidence bands on real data, Jev one Choice + none (trec-covid), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 21 | 0.905 | 0.143 |
| 0.5-0.9 | 24 | 1.000 | 0.000 |
| >=0.9 | 5 | 1.000 | 0.000 |

TypeSafe's confidence bands on real data, Jev tournament (6 groups, then final) (trec-covid), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 23 | 0.826 | 0.000 |
| 0.5-0.9 | 19 | 1.000 | 0.000 |
| >=0.9 | 8 | 1.000 | 0.000 |

Position bias (trec-covid): the same 30 passages sent in reverse order to Jev Choice. Same top pick 56% of the time (n=50); nDCG@10 0.750 normal vs 0.741 reversed; mean probability shift per passage 0.030; P(none) shift 0.014.

## bright-biology

103 queries; 39 have an answer in BM25's top 30 and are scored.

| Model | n | nDCG@10 | Top-1 | Recall@5 | MRR@10 | calls | median ms/call | p95 ms/call | median ms/query | $ per 1k queries | none-test AUROC | false accept @90% | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BM25 (floor) | 39 | 0.212 | 0.256 | 0.162 | 0.344 | 0 | — | — | 0 | 0.00 | 0.522 | 0.872 | — |
| Cohere Rerank 4 Pro | 39 | 0.414 | 0.513 | 0.346 | 0.638 | 142 | 723 | 1620 | 724 | 2.50 | 0.682 | 0.641 | 0.550* |
| Cohere Rerank 4 Fast | 39 | 0.396 | 0.462 | 0.319 | 0.606 | 142 | 592 | 1298 | 592 | 2.00 | 0.672 | 0.667 | 0.490* |
| ZeroEntropy zerank-2 | 39 | 0.430 | 0.564 | 0.379 | 0.683 | 142 | 605 | 2386 | 605 | 0.17 | 0.652 | 0.769 | 0.226* |
| DeepSeek V4.1 Flash P(yes) per pair | 39 | 0.321 | 0.436 | 0.307 | 0.522 | 4260 | 1206 | 1425 | 35971 | 0.99 | 0.590 | 1.000 | 0.071 |
| DeepSeek V4.1 Flash JSON, 30 in one call | 39 | 0.412 | 0.564 | 0.336 | 0.672 | 142 | 1814 | 2865 | 1815 | 0.62 | 0.662 | 0.769 | 0.068* |
| Jev yes/no per pair | 39 | 0.421 | 0.538 | 0.351 | 0.651 | 4260 | 268 | 364 | 8440 | 0.71 | 0.658 | 0.769 | 0.046 |
| Jev 30 yes/no in one call | 39 | 0.403 | 0.487 | 0.341 | 0.620 | 142 | 341 | 1232 | 341 | 0.26 | 0.652 | 0.821 | 0.078 |
| Jev one Choice + none | 39 | 0.425 | 0.615 | 0.332 | 0.697 | 142 | 280 | 1172 | 281 | 0.17 | 0.629 | 0.692 | 0.034* |
| Jev 4-level rubric, 30 in one call | 39 | 0.433 | 0.590 | 0.356 | 0.686 | 142 | 387 | 1456 | 387 | 0.29 | 0.677 | 0.795 | 0.246* |
| Jev 45 duels in one call (top 10) | 39 | 0.258 | 0.359 | 0.219 | 0.432 | 142 | 286 | 1018 | 287 | 0.16 | 0.529 | 0.846 | — |
| Jev tournament (6 groups, then final) | 39 | 0.427 | 0.615 | 0.301 | 0.672 | 284 | 294 | 866 | 607 | 0.25 | 0.636 | 0.744 | — |
| Jev cascade (batch prune, then 8 pairs) | 39 | 0.409 | 0.513 | 0.341 | 0.632 | 1278 | 264 | 345 | 2446 | 0.45 | 0.648 | 0.769 | — |
| Jev one Choice, passages reversed | 39 | 0.431 | 0.590 | 0.364 | 0.696 | 103 | 280 | 1176 | 280 | 0.17 | — | — | 0.032* |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | 39 | 0.188 | 0.205 | 0.131 | 0.292 | 142 | 198 | 231 | 198 | 0.04 | 0.574 | 0.821 | 0.218 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | 39 | 0.161 | 0.179 | 0.130 | 0.261 | 142 | 247 | 283 | 247 | 0.05 | 0.491 | 0.897 | 0.206* |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | 39 | 0.217 | 0.205 | 0.183 | 0.318 | 142 | 734 | 1342 | 734 | 0.18 | 0.530 | 0.872 | 0.219 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | 39 | 0.199 | 0.154 | 0.142 | 0.310 | 103 | 191 | 226 | 191 | 0.04 | — | — | 0.201* |
| Laya 421M yes/no per pair (self-hosted) | 39 | 0.240 | 0.179 | 0.194 | 0.330 | 142 | 130 | 270 | 130 | 0.02 | 0.545 | 0.872 | 0.409 |
| Laya 421M 4-level rubric per pair (self-hosted) | 39 | 0.207 | 0.154 | 0.176 | 0.281 | 142 | 139 | 274 | 139 | 0.03 | 0.528 | 0.846 | 0.463* |
| Laya multilingual 322M yes/no per pair (self-hosted) | 39 | 0.284 | 0.333 | 0.242 | 0.433 | 142 | 55 | 152 | 55 | 0.01 | 0.553 | 0.821 | 0.562 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | 39 | 0.128 | 0.128 | 0.085 | 0.205 | 142 | 77 | 201 | 77 | 0.02 | 0.514 | 0.897 | 0.541 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | 39 | 0.184 | 0.231 | 0.131 | 0.287 | 142 | 150 | 414 | 150 | 0.04 | 0.536 | 0.897 | 0.585 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | 39 | 0.227 | 0.256 | 0.167 | 0.350 | 142 | 221 | 690 | 221 | 0.06 | 0.527 | 0.846 | 0.360 |
| Open-Jev 2B yes/no per pair (self-hosted) | 39 | 0.334 | 0.410 | 0.264 | 0.516 | 4260 | 395 | 449 | 11898 | 0.29 | 0.579 | 0.846 | 0.070 |
| Open-Jev 9B yes/no per pair (self-hosted) | 39 | 0.359 | 0.410 | 0.284 | 0.553 | 4260 | 515 | 1115 | 15618 | 1.36 | 0.614 | 0.769 | 0.046 |
| Qwen3-Reranker-4B (self-hosted) | 39 | 0.373 | 0.487 | 0.300 | 0.602 | 142 | 1276 | 2845 | 1276 | 0.12 | 0.623 | 0.769 | — |
| bge-reranker-v2-m3 (self-hosted) | 39 | 0.249 | 0.308 | 0.201 | 0.408 | 142 | 498 | 1292 | 498 | 0.05 | 0.578 | 0.846 | — |
| mxbai-rerank-base-v2 (self-hosted) | 39 | 0.384 | 0.487 | 0.314 | 0.607 | 142 | 730 | 1535 | 730 | 0.07 | 0.626 | 0.846 | — |
| Qwen3.5-4B yes/no per pair (self-hosted) | 39 | 0.398 | 0.487 | 0.320 | 0.611 | 142 | 1900 | 2717 | 1900 | 0.15 | 0.658 | 0.718 | 0.043 |
| tev1-4B relevant / not per pair (self-hosted) | 39 | 0.410 | 0.564 | 0.318 | 0.658 | 142 | 2140 | 3217 | 2140 | 0.17 | 0.632 | 0.846 | 0.074 |
| reflex 4B yes/no per pair (self-hosted) | 39 | 0.393 | 0.436 | 0.350 | 0.611 | 4260 | 326 | 390 | 9742 | 0.36 | 0.642 | 0.718 | 0.028 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | 39 | 0.372 | 0.436 | 0.335 | 0.584 | 4260 | 363 | 506 | 11013 | 0.42 | 0.614 | 0.769 | 0.057 |
| decider-2b v11 yes/no per pair (self-hosted) | 39 | 0.437 | 0.564 | 0.359 | 0.702 | 4260 | 1006 | 1442 | 30819 | 0.07 | 0.674 | 0.615 | 0.149 |

Jev Choice's own nothing-relevant signals (bright-biology):

| signal | AUROC | false accept @90% | median with answer | median without |
|---|---|---|---|---|
| max_score | 0.629 | 0.692 | 0.670 | 0.500 |
| 1-P(none) | 0.671 | 0.718 | 0.980 | 0.790 |
| P(any) | 0.672 | 0.769 | 0.910 | 0.750 |

TypeSafe's confidence bands on real data, Jev one Choice + none (bright-biology), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 8 | 0.500 | 0.250 |
| 0.5-0.9 | 21 | 0.619 | 0.190 |
| >=0.9 | 10 | 0.700 | 0.000 |

TypeSafe's confidence bands on real data, Jev tournament (6 groups, then final) (bright-biology), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 11 | 0.364 | 0.000 |
| 0.5-0.9 | 14 | 0.786 | 0.000 |
| >=0.9 | 14 | 0.643 | 0.000 |

Position bias (bright-biology): the same 30 passages sent in reverse order to Jev Choice. Same top pick 74% of the time (n=39); nDCG@10 0.425 normal vs 0.431 reversed; mean probability shift per passage 0.012; P(none) shift 0.031.

## bright-economics

103 queries; 38 have an answer in BM25's top 30 and are scored.

| Model | n | nDCG@10 | Top-1 | Recall@5 | MRR@10 | calls | median ms/call | p95 ms/call | median ms/query | $ per 1k queries | none-test AUROC | false accept @90% | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BM25 (floor) | 38 | 0.280 | 0.184 | 0.207 | 0.308 | 0 | — | — | 0 | 0.00 | 0.520 | 0.895 | — |
| Cohere Rerank 4 Pro | 38 | 0.442 | 0.368 | 0.348 | 0.565 | 141 | 870 | 1673 | 870 | 2.50 | 0.590 | 0.763 | 0.472* |
| Cohere Rerank 4 Fast | 38 | 0.490 | 0.474 | 0.378 | 0.634 | 141 | 644 | 1324 | 645 | 2.00 | 0.588 | 0.816 | 0.416* |
| ZeroEntropy zerank-2 | 38 | 0.479 | 0.500 | 0.398 | 0.627 | 141 | 756 | 1679 | 756 | 0.28 | 0.596 | 0.763 | 0.247* |
| DeepSeek V4.1 Flash P(yes) per pair | 38 | 0.374 | 0.368 | 0.294 | 0.466 | 4230 | 1150 | 1539 | 35748 | 1.49 | 0.592 | 1.000 | 0.115 |
| DeepSeek V4.1 Flash JSON, 30 in one call | 38 | 0.549 | 0.579 | 0.417 | 0.695 | 141 | 2478 | 3495 | 2478 | 1.04 | 0.635 | 0.711 | 0.061* |
| Jev yes/no per pair | 38 | 0.487 | 0.500 | 0.397 | 0.649 | 4230 | 273 | 366 | 8541 | 0.92 | 0.612 | 0.711 | 0.026 |
| Jev 30 yes/no in one call | 38 | 0.508 | 0.526 | 0.408 | 0.662 | 141 | 497 | 1472 | 498 | 0.38 | 0.632 | 0.711 | 0.045 |
| Jev one Choice + none | 38 | 0.524 | 0.632 | 0.408 | 0.743 | 141 | 321 | 1179 | 321 | 0.30 | 0.621 | 0.763 | 0.080* |
| Jev 4-level rubric, 30 in one call | 38 | 0.529 | 0.605 | 0.406 | 0.695 | 141 | 522 | 1587 | 522 | 0.42 | 0.645 | 0.658 | 0.229* |
| Jev 45 duels in one call (top 10) | 38 | 0.396 | 0.447 | 0.293 | 0.511 | 141 | 320 | 1231 | 320 | 0.20 | 0.520 | 0.789 | — |
| Jev tournament (6 groups, then final) | 38 | 0.538 | 0.658 | 0.399 | 0.748 | 282 | 304 | 964 | 710 | 0.40 | 0.638 | 0.737 | — |
| Jev cascade (batch prune, then 8 pairs) | 38 | 0.493 | 0.474 | 0.394 | 0.617 | 1269 | 275 | 417 | 2600 | 0.64 | 0.614 | 0.737 | — |
| Jev one Choice, passages reversed | 38 | 0.516 | 0.553 | 0.429 | 0.695 | 103 | 374 | 1005 | 375 | 0.30 | — | — | 0.083* |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | 38 | 0.206 | 0.158 | 0.147 | 0.248 | 141 | 303 | 576 | 303 | 0.07 | 0.535 | 0.842 | 0.131 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | 38 | 0.246 | 0.184 | 0.173 | 0.297 | 141 | 357 | 636 | 357 | 0.08 | 0.501 | 0.974 | 0.153* |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | 38 | 0.233 | 0.184 | 0.130 | 0.274 | 141 | 825 | 1352 | 825 | 0.19 | 0.511 | 0.921 | 0.179 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | 38 | 0.213 | 0.158 | 0.136 | 0.261 | 103 | 295 | 561 | 295 | 0.07 | — | — | 0.130* |
| Laya 421M yes/no per pair (self-hosted) | 38 | 0.307 | 0.211 | 0.295 | 0.340 | 141 | 144 | 272 | 144 | 0.03 | 0.533 | 0.868 | 0.398 |
| Laya 421M 4-level rubric per pair (self-hosted) | 38 | 0.350 | 0.237 | 0.294 | 0.411 | 141 | 144 | 274 | 144 | 0.03 | 0.536 | 0.842 | 0.433* |
| Laya multilingual 322M yes/no per pair (self-hosted) | 38 | 0.242 | 0.158 | 0.156 | 0.296 | 141 | 134 | 261 | 134 | 0.03 | 0.520 | 0.868 | 0.510 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | 38 | 0.183 | 0.105 | 0.174 | 0.199 | 141 | 234 | 454 | 234 | 0.05 | 0.495 | 0.895 | 0.528 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | 38 | 0.213 | 0.158 | 0.191 | 0.303 | 141 | 460 | 941 | 460 | 0.10 | 0.516 | 0.895 | 0.585 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | 38 | 0.246 | 0.211 | 0.153 | 0.299 | 141 | 744 | 1815 | 744 | 0.16 | 0.507 | 0.895 | 0.325 |
| Open-Jev 2B yes/no per pair (self-hosted) | 38 | 0.213 | 0.158 | 0.125 | 0.249 | 4230 | 423 | 510 | 12742 | 0.32 | 0.544 | 0.842 | 0.107 |
| Open-Jev 9B yes/no per pair (self-hosted) | 38 | 0.423 | 0.421 | 0.333 | 0.558 | 4230 | 574 | 1400 | 18172 | 1.61 | 0.596 | 0.816 | 0.091 |
| Qwen3-Reranker-4B (self-hosted) | 38 | 0.366 | 0.263 | 0.307 | 0.426 | 141 | 3230 | 4792 | 3230 | 0.25 | 0.568 | 0.737 | — |
| bge-reranker-v2-m3 (self-hosted) | 38 | 0.198 | 0.079 | 0.198 | 0.211 | 141 | 1248 | 2096 | 1248 | 0.10 | 0.505 | 0.868 | — |
| mxbai-rerank-base-v2 (self-hosted) | 38 | 0.287 | 0.184 | 0.202 | 0.313 | 141 | 1754 | 2594 | 1754 | 0.13 | 0.525 | 0.895 | — |
| Qwen3.5-4B yes/no per pair (self-hosted) | 38 | 0.426 | 0.421 | 0.368 | 0.556 | 141 | 2520 | 4030 | 2520 | 0.21 | 0.625 | 0.684 | 0.071 |
| tev1-4B relevant / not per pair (self-hosted) | 38 | 0.427 | 0.421 | 0.362 | 0.534 | 141 | 2974 | 4529 | 2974 | 0.24 | 0.590 | 0.789 | 0.071 |
| reflex 4B yes/no per pair (self-hosted) | 38 | 0.384 | 0.316 | 0.310 | 0.454 | 4230 | 350 | 410 | 10396 | 0.39 | 0.572 | 0.789 | 0.049 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | 38 | 0.409 | 0.368 | 0.356 | 0.513 | 4230 | 503 | 760 | 15309 | 0.58 | 0.594 | 0.842 | 0.091 |
| decider-2b v11 yes/no per pair (self-hosted) | 38 | 0.437 | 0.421 | 0.312 | 0.552 | 4230 | 1261 | 2276 | 39491 | 0.10 | 0.611 | 0.816 | 0.134 |

Jev Choice's own nothing-relevant signals (bright-economics):

| signal | AUROC | false accept @90% | median with answer | median without |
|---|---|---|---|---|
| max_score | 0.621 | 0.763 | 0.470 | 0.370 |
| 1-P(none) | 0.642 | 0.684 | 0.880 | 0.755 |
| P(any) | 0.648 | 0.658 | 0.700 | 0.585 |

TypeSafe's confidence bands on real data, Jev one Choice + none (bright-economics), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 25 | 0.640 | 0.240 |
| 0.5-0.9 | 9 | 0.556 | 0.000 |
| >=0.9 | 4 | 0.750 | 0.000 |

TypeSafe's confidence bands on real data, Jev tournament (6 groups, then final) (bright-economics), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 15 | 0.800 | 0.000 |
| 0.5-0.9 | 20 | 0.550 | 0.000 |
| >=0.9 | 3 | 0.667 | 0.000 |

Position bias (bright-economics): the same 30 passages sent in reverse order to Jev Choice. Same top pick 61% of the time (n=38); nDCG@10 0.524 normal vs 0.516 reversed; mean probability shift per passage 0.013; P(none) shift 0.045.

## bright-earth_science

116 queries; 57 have an answer in BM25's top 30 and are scored.

| Model | n | nDCG@10 | Top-1 | Recall@5 | MRR@10 | calls | median ms/call | p95 ms/call | median ms/query | $ per 1k queries | none-test AUROC | false accept @90% | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BM25 (floor) | 57 | 0.261 | 0.228 | 0.188 | 0.334 | 0 | — | — | 0 | 0.00 | 0.527 | 0.877 | — |
| Cohere Rerank 4 Pro | 57 | 0.492 | 0.667 | 0.439 | 0.761 | 173 | 787 | 1468 | 852 | 2.50 | 0.703 | 0.649 | 0.400* |
| Cohere Rerank 4 Fast | 57 | 0.477 | 0.596 | 0.408 | 0.723 | 173 | 604 | 1368 | 636 | 2.00 | 0.639 | 0.667 | 0.360* |
| ZeroEntropy zerank-2 | 57 | 0.480 | 0.614 | 0.415 | 0.725 | 173 | 575 | 1281 | 575 | 0.19 | 0.649 | 0.649 | 0.194* |
| DeepSeek V4.1 Flash P(yes) per pair | 57 | 0.329 | 0.333 | 0.261 | 0.468 | 5190 | 1082 | 1401 | 33301 | 1.20 | 0.649 | 1.000 | 0.093 |
| DeepSeek V4.1 Flash JSON, 30 in one call | 57 | 0.460 | 0.649 | 0.375 | 0.712 | 173 | 1989 | 2819 | 1989 | 0.75 | 0.700 | 0.579 | 0.076* |
| Jev yes/no per pair | 57 | 0.445 | 0.579 | 0.390 | 0.688 | 5190 | 268 | 363 | 8564 | 0.75 | 0.693 | 0.614 | 0.031 |
| Jev 30 yes/no in one call | 57 | 0.465 | 0.579 | 0.410 | 0.694 | 173 | 464 | 1379 | 533 | 0.30 | 0.692 | 0.596 | 0.065 |
| Jev one Choice + none | 57 | 0.441 | 0.632 | 0.377 | 0.721 | 173 | 467 | 1214 | 471 | 0.22 | 0.735 | 0.544 | 0.048* |
| Jev 4-level rubric, 30 in one call | 57 | 0.475 | 0.632 | 0.410 | 0.720 | 173 | 531 | 1600 | 563 | 0.33 | 0.714 | 0.561 | 0.216* |
| Jev 45 duels in one call (top 10) | 57 | 0.328 | 0.439 | 0.299 | 0.521 | 173 | 291 | 22288 | 291 | 0.17 | 0.608 | 0.825 | — |
| Jev tournament (6 groups, then final) | 57 | 0.444 | 0.614 | 0.341 | 0.709 | 346 | 289 | 1160 | 728 | 0.30 | 0.746 | 0.474 | — |
| Jev cascade (batch prune, then 8 pairs) | 57 | 0.457 | 0.579 | 0.399 | 0.692 | 1557 | 274 | 467 | 2743 | 0.51 | 0.690 | 0.632 | — |
| Jev one Choice, passages reversed | 57 | 0.479 | 0.684 | 0.391 | 0.765 | 173 | 396 | 1192 | 396 | 0.22 | 0.751 | 0.561 | 0.045* |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | 57 | 0.114 | 0.088 | 0.081 | 0.165 | 173 | 225 | 297 | 225 | 0.05 | 0.465 | 0.930 | 0.177 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | 57 | 0.117 | 0.035 | 0.076 | 0.150 | 173 | 275 | 353 | 275 | 0.06 | 0.544 | 0.895 | 0.117* |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | 57 | 0.268 | 0.193 | 0.225 | 0.355 | 173 | 715 | 1353 | 715 | 0.18 | 0.518 | 0.877 | 0.149 |
| Laya 421M yes/no per pair (self-hosted) | 57 | 0.290 | 0.193 | 0.278 | 0.363 | 173 | 143 | 269 | 143 | 0.03 | 0.526 | 0.895 | 0.278 |
| Laya 421M 4-level rubric per pair (self-hosted) | 57 | 0.247 | 0.158 | 0.213 | 0.309 | 173 | 143 | 270 | 143 | 0.03 | 0.526 | 0.825 | 0.380* |
| Laya multilingual 322M yes/no per pair (self-hosted) | 57 | 0.289 | 0.281 | 0.263 | 0.396 | 173 | 88 | 231 | 88 | 0.02 | 0.525 | 0.842 | 0.445 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | 57 | 0.288 | 0.193 | 0.251 | 0.362 | 173 | 127 | 300 | 127 | 0.03 | 0.524 | 0.895 | 0.157 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | 57 | 0.228 | 0.193 | 0.211 | 0.321 | 173 | 257 | 620 | 257 | 0.06 | 0.520 | 0.860 | 0.206 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | 57 | 0.350 | 0.368 | 0.319 | 0.506 | 173 | 399 | 954 | 399 | 0.09 | 0.566 | 0.842 | 0.082 |
| Open-Jev 2B yes/no per pair (self-hosted) | 57 | 0.352 | 0.351 | 0.304 | 0.497 | 5190 | 401 | 455 | 12064 | 0.29 | 0.595 | 0.860 | 0.031 |
| Open-Jev 9B yes/no per pair (self-hosted) | 57 | 0.433 | 0.509 | 0.395 | 0.631 | 5190 | 596 | 1131 | 17981 | 1.58 | 0.651 | 0.719 | 0.062 |
| Qwen3-Reranker-4B (self-hosted) | 57 | 0.395 | 0.421 | 0.342 | 0.570 | 173 | 2120 | 3319 | 2120 | 0.16 | 0.611 | 0.719 | — |
| bge-reranker-v2-m3 (self-hosted) | 57 | 0.410 | 0.439 | 0.328 | 0.582 | 173 | 801 | 1375 | 801 | 0.06 | 0.578 | 0.772 | — |
| mxbai-rerank-base-v2 (self-hosted) | 57 | 0.372 | 0.404 | 0.327 | 0.509 | 173 | 1158 | 1757 | 1158 | 0.09 | 0.581 | 0.789 | — |
| Qwen3.5-4B yes/no per pair (self-hosted) | 57 | 0.442 | 0.509 | 0.338 | 0.650 | 173 | 1958 | 2747 | 1958 | 0.16 | 0.641 | 0.719 | 0.055 |
| tev1-4B relevant / not per pair (self-hosted) | 57 | 0.436 | 0.579 | 0.350 | 0.680 | 173 | 2320 | 3204 | 2320 | 0.19 | 0.667 | 0.737 | 0.046 |
| reflex 4B yes/no per pair (self-hosted) | 57 | 0.391 | 0.439 | 0.312 | 0.580 | 5190 | 325 | 376 | 9715 | 0.36 | 0.625 | 0.772 | 0.028 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | 57 | 0.405 | 0.491 | 0.321 | 0.615 | 5190 | 395 | 557 | 11989 | 0.47 | 0.668 | 0.684 | 0.075 |
| decider-2b v11 yes/no per pair (self-hosted) | 57 | 0.479 | 0.544 | 0.421 | 0.694 | 5190 | 998 | 1426 | 30398 | 0.07 | 0.645 | 0.754 | 0.110 |

Jev Choice's own nothing-relevant signals (bright-earth_science):

| signal | AUROC | false accept @90% | median with answer | median without |
|---|---|---|---|---|
| max_score | 0.735 | 0.544 | 0.640 | 0.380 |
| 1-P(none) | 0.692 | 0.579 | 0.940 | 0.720 |
| P(any) | 0.671 | 0.579 | 0.800 | 0.560 |

TypeSafe's confidence bands on real data, Jev one Choice + none (bright-earth_science), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 12 | 0.417 | 0.167 |
| 0.5-0.9 | 34 | 0.647 | 0.059 |
| >=0.9 | 11 | 0.818 | 0.091 |

TypeSafe's confidence bands on real data, Jev tournament (6 groups, then final) (bright-earth_science), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 13 | 0.231 | 0.000 |
| 0.5-0.9 | 30 | 0.700 | 0.000 |
| >=0.9 | 14 | 0.786 | 0.000 |

Position bias (bright-earth_science): the same 30 passages sent in reverse order to Jev Choice. Same top pick 84% of the time (n=57); nDCG@10 0.441 normal vs 0.479 reversed; mean probability shift per passage 0.011; P(none) shift 0.041.

## bright-psychology

101 queries; 29 have an answer in BM25's top 30 and are scored.

| Model | n | nDCG@10 | Top-1 | Recall@5 | MRR@10 | calls | median ms/call | p95 ms/call | median ms/query | $ per 1k queries | none-test AUROC | false accept @90% | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BM25 (floor) | 29 | 0.266 | 0.138 | 0.252 | 0.280 | 0 | — | — | 0 | 0.00 | 0.510 | 0.897 | — |
| Cohere Rerank 4 Pro | 29 | 0.626 | 0.690 | 0.542 | 0.792 | 130 | 845 | 1670 | 1052 | 2.50 | 0.727 | 0.517 | 0.424* |
| Cohere Rerank 4 Fast | 29 | 0.633 | 0.724 | 0.536 | 0.806 | 130 | 650 | 1528 | 653 | 2.00 | 0.699 | 0.517 | 0.358* |
| ZeroEntropy zerank-2 | 29 | 0.629 | 0.690 | 0.564 | 0.807 | 130 | 2560 | 3579 | 2856 | 0.24 | 0.727 | 0.655 | 0.201* |
| DeepSeek V4.1 Flash P(yes) per pair | 29 | 0.417 | 0.414 | 0.391 | 0.538 | 3900 | 1071 | 1436 | 33033 | 1.33 | 0.638 | 1.000 | 0.090 |
| DeepSeek V4.1 Flash JSON, 30 in one call | 29 | 0.657 | 0.862 | 0.556 | 0.912 | 130 | 2364 | 2998 | 2364 | 0.88 | 0.744 | 0.552 | 0.051* |
| Jev yes/no per pair | 29 | 0.600 | 0.655 | 0.541 | 0.764 | 3900 | 264 | 356 | 8676 | 0.83 | 0.723 | 0.586 | 0.023 |
| Jev 30 yes/no in one call | 29 | 0.628 | 0.655 | 0.540 | 0.778 | 130 | 521 | 22475 | 673 | 0.33 | 0.737 | 0.517 | 0.038 |
| Jev one Choice + none | 29 | 0.571 | 0.690 | 0.498 | 0.811 | 130 | 469 | 1269 | 482 | 0.25 | 0.731 | 0.483 | 0.064* |
| Jev 4-level rubric, 30 in one call | 29 | 0.652 | 0.724 | 0.555 | 0.822 | 130 | 653 | 1640 | 807 | 0.37 | 0.741 | 0.483 | 0.174* |
| Jev 45 duels in one call (top 10) | 29 | 0.441 | 0.586 | 0.379 | 0.621 | 130 | 304 | 22251 | 305 | 0.18 | 0.665 | 0.724 | — |
| Jev tournament (6 groups, then final) | 29 | 0.586 | 0.690 | 0.428 | 0.796 | 260 | 298 | 1279 | 766 | 0.35 | 0.725 | 0.552 | — |
| Jev cascade (batch prune, then 8 pairs) | 29 | 0.605 | 0.621 | 0.554 | 0.754 | 1170 | 275 | 478 | 2695 | 0.57 | 0.737 | 0.586 | — |
| Jev one Choice, passages reversed | 29 | 0.571 | 0.655 | 0.515 | 0.783 | 130 | 451 | 1177 | 451 | 0.25 | 0.751 | 0.448 | 0.068* |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | 29 | 0.229 | 0.241 | 0.111 | 0.317 | 130 | 264 | 436 | 264 | 0.06 | 0.598 | 0.793 | 0.135 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | 29 | 0.173 | 0.138 | 0.116 | 0.234 | 130 | 320 | 498 | 320 | 0.07 | 0.535 | 0.793 | 0.207* |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | 29 | 0.310 | 0.138 | 0.331 | 0.344 | 130 | 761 | 1504 | 761 | 0.19 | 0.545 | 0.897 | 0.141 |
| Laya 421M yes/no per pair (self-hosted) | 29 | 0.392 | 0.276 | 0.368 | 0.475 | 130 | 144 | 272 | 144 | 0.03 | 0.520 | 0.828 | 0.295 |
| Laya 421M 4-level rubric per pair (self-hosted) | 29 | 0.378 | 0.276 | 0.314 | 0.454 | 130 | 144 | 286 | 144 | 0.03 | 0.555 | 0.793 | 0.367* |
| Laya multilingual 322M yes/no per pair (self-hosted) | 29 | 0.372 | 0.241 | 0.333 | 0.431 | 130 | 116 | 198 | 116 | 0.02 | 0.524 | 0.897 | 0.430 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | 29 | 0.228 | 0.172 | 0.255 | 0.301 | 130 | 198 | 333 | 198 | 0.04 | 0.514 | 0.897 | 0.319 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | 29 | 0.203 | 0.138 | 0.195 | 0.257 | 130 | 404 | 687 | 404 | 0.08 | 0.517 | 0.828 | 0.395 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | 29 | 0.312 | 0.241 | 0.261 | 0.369 | 130 | 643 | 1174 | 643 | 0.13 | 0.532 | 0.828 | 0.254 |
| Open-Jev 2B yes/no per pair (self-hosted) | 29 | 0.477 | 0.552 | 0.483 | 0.666 | 3900 | 418 | 491 | 12717 | 0.31 | 0.651 | 0.690 | 0.047 |
| Open-Jev 9B yes/no per pair (self-hosted) | 29 | 0.560 | 0.655 | 0.484 | 0.748 | 3900 | 561 | 1261 | 17204 | 1.55 | 0.699 | 0.655 | 0.071 |
| Qwen3-Reranker-4B (self-hosted) | 29 | 0.562 | 0.655 | 0.529 | 0.724 | 130 | 2799 | 3883 | 2799 | 0.21 | 0.703 | 0.552 | — |
| bge-reranker-v2-m3 (self-hosted) | 29 | 0.376 | 0.276 | 0.377 | 0.456 | 130 | 1181 | 1614 | 1181 | 0.09 | 0.586 | 0.793 | — |
| mxbai-rerank-base-v2 (self-hosted) | 29 | 0.543 | 0.483 | 0.544 | 0.652 | 130 | 1512 | 2047 | 1512 | 0.11 | 0.623 | 0.759 | — |
| Qwen3.5-4B yes/no per pair (self-hosted) | 29 | 0.562 | 0.586 | 0.547 | 0.752 | 130 | 2305 | 3339 | 2305 | 0.18 | 0.690 | 0.724 | 0.046 |
| tev1-4B relevant / not per pair (self-hosted) | 29 | 0.588 | 0.655 | 0.548 | 0.754 | 130 | 2665 | 3809 | 2665 | 0.21 | 0.672 | 0.655 | 0.040 |
| reflex 4B yes/no per pair (self-hosted) | 29 | 0.570 | 0.690 | 0.440 | 0.780 | 3900 | 340 | 391 | 10086 | 0.38 | 0.735 | 0.621 | 0.025 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | 29 | 0.567 | 0.655 | 0.460 | 0.741 | 3900 | 436 | 645 | 13562 | 0.52 | 0.707 | 0.586 | 0.083 |
| decider-2b v11 yes/no per pair (self-hosted) | 29 | 0.608 | 0.621 | 0.512 | 0.743 | 3900 | 1097 | 1896 | 31839 | 0.08 | 0.708 | 0.621 | 0.116 |

Jev Choice's own nothing-relevant signals (bright-psychology):

| signal | AUROC | false accept @90% | median with answer | median without |
|---|---|---|---|---|
| max_score | 0.731 | 0.483 | 0.720 | 0.390 |
| 1-P(none) | 0.731 | 0.483 | 0.910 | 0.660 |
| P(any) | 0.728 | 0.552 | 0.760 | 0.470 |

TypeSafe's confidence bands on real data, Jev one Choice + none (bright-psychology), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 7 | 0.286 | 0.143 |
| 0.5-0.9 | 14 | 0.714 | 0.071 |
| >=0.9 | 8 | 1.000 | 0.000 |

TypeSafe's confidence bands on real data, Jev tournament (6 groups, then final) (bright-psychology), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 4 | 0.250 | 0.000 |
| 0.5-0.9 | 15 | 0.600 | 0.000 |
| >=0.9 | 10 | 1.000 | 0.000 |

Position bias (bright-psychology): the same 30 passages sent in reverse order to Jev Choice. Same top pick 90% of the time (n=29); nDCG@10 0.571 normal vs 0.571 reversed; mean probability shift per passage 0.008; P(none) shift 0.034.

## bright-robotics

101 queries; 35 have an answer in BM25's top 30 and are scored.

| Model | n | nDCG@10 | Top-1 | Recall@5 | MRR@10 | calls | median ms/call | p95 ms/call | median ms/query | $ per 1k queries | none-test AUROC | false accept @90% | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BM25 (floor) | 35 | 0.180 | 0.114 | 0.151 | 0.231 | 0 | — | — | 0 | 0.00 | 0.504 | 0.914 | — |
| Cohere Rerank 4 Pro | 35 | 0.464 | 0.543 | 0.372 | 0.650 | 136 | 1090 | 1980 | 1392 | 3.04 | 0.667 | 0.743 | 0.561* |
| Cohere Rerank 4 Fast | 35 | 0.382 | 0.429 | 0.356 | 0.539 | 136 | 678 | 1850 | 817 | 2.44 | 0.634 | 0.800 | 0.477* |
| ZeroEntropy zerank-2 | 35 | 0.483 | 0.571 | 0.445 | 0.693 | 136 | 2129 | 3255 | 2215 | 0.33 | 0.664 | 0.800 | 0.178* |
| DeepSeek V4.1 Flash P(yes) per pair | 35 | 0.326 | 0.343 | 0.297 | 0.439 | 4080 | 1070 | 1405 | 32720 | 1.60 | 0.586 | 1.000 | 0.103 |
| DeepSeek V4.1 Flash JSON, 30 in one call | 35 | 0.445 | 0.543 | 0.371 | 0.617 | 136 | 2270 | 3102 | 2270 | 1.03 | 0.658 | 1.000 | 0.065* |
| Jev yes/no per pair | 35 | 0.479 | 0.629 | 0.402 | 0.717 | 4080 | 260 | 339 | 8543 | 1.47 | 0.667 | 0.800 | 0.050 |
| Jev 30 yes/no in one call | 35 | 0.479 | 0.571 | 0.390 | 0.667 | 136 | 498 | 22587 | 537 | 0.37 | 0.680 | 0.743 | 0.065 |
| Jev one Choice + none | 35 | 0.469 | 0.629 | 0.388 | 0.718 | 136 | 461 | 1289 | 461 | 0.29 | 0.649 | 0.686 | 0.042* |
| Jev 4-level rubric, 30 in one call | 35 | 0.478 | 0.571 | 0.392 | 0.670 | 136 | 581 | 22490 | 1114 | 0.41 | 0.681 | 0.686 | 0.247* |
| Jev 45 duels in one call (top 10) | 35 | 0.277 | 0.400 | 0.233 | 0.446 | 136 | 301 | 22287 | 301 | 0.22 | 0.655 | 0.800 | — |
| Jev tournament (6 groups, then final) | 35 | 0.458 | 0.629 | 0.339 | 0.709 | 272 | 288 | 22234 | 623 | 0.41 | 0.666 | 0.743 | — |
| Jev cascade (batch prune, then 8 pairs) | 35 | 0.486 | 0.629 | 0.403 | 0.715 | 1224 | 266 | 478 | 2628 | 0.77 | 0.679 | 0.714 | — |
| Jev one Choice, passages reversed | 35 | 0.454 | 0.600 | 0.381 | 0.700 | 136 | 333 | 1197 | 333 | 0.29 | 0.606 | 0.629 | 0.043* |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | 35 | 0.145 | 0.057 | 0.110 | 0.165 | 136 | 262 | 718 | 262 | 0.10 | 0.620 | 0.629 | 0.153 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | 35 | 0.123 | 0.086 | 0.069 | 0.159 | 136 | 321 | 1333 | 321 | 0.12 | 0.558 | 0.857 | 0.142* |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | 35 | 0.298 | 0.257 | 0.289 | 0.397 | 136 | 1149 | 3070 | 1149 | 0.25 | 0.522 | 0.886 | 0.134 |
| Laya 421M yes/no per pair (self-hosted) | 35 | 0.202 | 0.114 | 0.178 | 0.254 | 136 | 144 | 273 | 144 | 0.03 | 0.516 | 0.914 | 0.487 |
| Laya 421M 4-level rubric per pair (self-hosted) | 35 | 0.227 | 0.114 | 0.210 | 0.292 | 136 | 144 | 275 | 144 | 0.03 | 0.498 | 0.914 | 0.516* |
| Laya multilingual 322M yes/no per pair (self-hosted) | 35 | 0.205 | 0.143 | 0.182 | 0.257 | 136 | 149 | 264 | 149 | 0.03 | 0.519 | 0.914 | 0.566 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | 35 | 0.130 | 0.057 | 0.127 | 0.167 | 136 | 283 | 7016 | 283 | 0.20 | 0.501 | 0.943 | 0.272 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | 35 | 0.229 | 0.229 | 0.191 | 0.349 | 136 | 595 | 11237 | 595 | 0.37 | 0.509 | 0.914 | 0.189 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | 35 | 0.208 | 0.200 | 0.131 | 0.287 | 135 | 992 | 18039 | 992 | 0.49 | 0.502 | 0.914 | 0.116 |
| Open-Jev 2B yes/no per pair (self-hosted) | 35 | 0.168 | 0.143 | 0.122 | 0.220 | 4080 | 458 | 1162 | 13697 | 0.58 | 0.521 | 0.914 | 0.085 |
| Open-Jev 9B yes/no per pair (self-hosted) | 35 | 0.325 | 0.286 | 0.332 | 0.430 | 4080 | 643 | 1784 | 19555 | 2.55 | 0.547 | 0.914 | 0.052 |
| Qwen3-Reranker-4B (self-hosted) | 35 | 0.445 | 0.457 | 0.371 | 0.578 | 136 | 3296 | 26404 | 3296 | 0.48 | 0.656 | 0.743 | — |
| bge-reranker-v2-m3 (self-hosted) | 35 | 0.243 | 0.171 | 0.281 | 0.298 | 136 | 1607 | 19108 | 1607 | 0.25 | 0.524 | 0.886 | — |
| mxbai-rerank-base-v2 (self-hosted) | 35 | 0.347 | 0.343 | 0.336 | 0.482 | 136 | 1761 | 13291 | 1761 | 0.26 | 0.571 | 0.829 | — |
| Qwen3.5-4B yes/no per pair (self-hosted) | 35 | 0.399 | 0.457 | 0.363 | 0.563 | 136 | 2747 | 19091 | 2747 | 0.36 | 0.634 | 0.857 | 0.060 |
| tev1-4B relevant / not per pair (self-hosted) | 35 | 0.381 | 0.400 | 0.364 | 0.530 | 136 | 3279 | 20443 | 3279 | 0.42 | 0.585 | 0.886 | 0.163 |
| reflex 4B yes/no per pair (self-hosted) | 35 | 0.347 | 0.286 | 0.335 | 0.437 | 4080 | 378 | 1043 | 10822 | 0.55 | 0.572 | 0.857 | 0.089 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | 35 | 0.406 | 0.371 | 0.392 | 0.535 | 4080 | 676 | 3359 | 20091 | 1.13 | 0.615 | 0.857 | 0.090 |
| decider-2b v11 yes/no per pair (self-hosted) | 35 | 0.417 | 0.457 | 0.400 | 0.578 | 4080 | 2668 | 6158 | 82117 | 0.18 | 0.662 | 0.829 | 0.200 |

Jev Choice's own nothing-relevant signals (bright-robotics):

| signal | AUROC | false accept @90% | median with answer | median without |
|---|---|---|---|---|
| max_score | 0.649 | 0.686 | 0.500 | 0.370 |
| 1-P(none) | 0.668 | 0.686 | 0.900 | 0.800 |
| P(any) | 0.680 | 0.714 | 0.760 | 0.600 |

TypeSafe's confidence bands on real data, Jev one Choice + none (bright-robotics), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 18 | 0.611 | 0.389 |
| 0.5-0.9 | 15 | 0.600 | 0.067 |
| >=0.9 | 2 | 1.000 | 0.000 |

TypeSafe's confidence bands on real data, Jev tournament (6 groups, then final) (bright-robotics), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 16 | 0.562 | 0.000 |
| 0.5-0.9 | 12 | 0.667 | 0.000 |
| >=0.9 | 7 | 0.714 | 0.000 |

Position bias (bright-robotics): the same 30 passages sent in reverse order to Jev Choice. Same top pick 74% of the time (n=35); nDCG@10 0.469 normal vs 0.454 reversed; mean probability shift per passage 0.013; P(none) shift 0.049.

## bright-stackoverflow

117 queries; 62 have an answer in BM25's top 30 and are scored.

| Model | n | nDCG@10 | Top-1 | Recall@5 | MRR@10 | calls | median ms/call | p95 ms/call | median ms/query | $ per 1k queries | none-test AUROC | false accept @90% | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BM25 (floor) | 62 | 0.268 | 0.274 | 0.207 | 0.378 | 0 | — | — | 0 | 0.00 | 0.514 | 0.887 | — |
| Cohere Rerank 4 Pro | 62 | 0.341 | 0.290 | 0.279 | 0.478 | 179 | 1513 | 2946 | 1868 | 2.61 | 0.563 | 0.839 | 0.432* |
| Cohere Rerank 4 Fast | 62 | 0.339 | 0.306 | 0.287 | 0.486 | 179 | 762 | 1745 | 808 | 2.09 | 0.574 | 0.806 | 0.364* |
| ZeroEntropy zerank-2 | 62 | 0.362 | 0.371 | 0.298 | 0.523 | 179 | 2928 | 3432 | 3031 | 0.56 | 0.593 | 0.887 | 0.119* |
| DeepSeek V4.1 Flash P(yes) per pair | 62 | 0.327 | 0.339 | 0.284 | 0.469 | 5370 | 1078 | 1459 | 33814 | 2.55 | 0.524 | 1.000 | 0.115 |
| DeepSeek V4.1 Flash JSON, 30 in one call | 62 | 0.378 | 0.387 | 0.307 | 0.538 | 179 | 2509 | 3646 | 2509 | 2.16 | 0.586 | 1.000 | 0.068* |
| Jev yes/no per pair | 62 | 0.363 | 0.387 | 0.301 | 0.544 | 5370 | 269 | 351 | 8491 | 1.49 | 0.591 | 0.839 | 0.034 |
| Jev 30 yes/no in one call | 62 | 0.370 | 0.339 | 0.319 | 0.543 | 179 | 695 | 22307 | 695 | 0.72 | 0.588 | 0.855 | 0.061 |
| Jev one Choice + none | 62 | 0.371 | 0.371 | 0.336 | 0.539 | 179 | 522 | 22465 | 667 | 0.64 | 0.538 | 0.871 | 0.069* |
| Jev 4-level rubric, 30 in one call | 62 | 0.375 | 0.371 | 0.326 | 0.549 | 179 | 775 | 23018 | 775 | 0.75 | 0.598 | 0.855 | 0.166* |
| Jev 45 duels in one call (top 10) | 62 | 0.306 | 0.339 | 0.257 | 0.469 | 179 | 355 | 22266 | 355 | 0.32 | 0.538 | 0.887 | — |
| Jev tournament (6 groups, then final) | 62 | 0.342 | 0.355 | 0.231 | 0.521 | 358 | 321 | 1947 | 806 | 0.80 | 0.552 | 0.726 | — |
| Jev cascade (batch prune, then 8 pairs) | 62 | 0.379 | 0.387 | 0.320 | 0.555 | 1611 | 263 | 556 | 2720 | 1.11 | 0.592 | 0.806 | — |
| Jev one Choice, passages reversed | 62 | 0.394 | 0.452 | 0.319 | 0.591 | 179 | 702 | 1641 | 702 | 0.64 | 0.580 | 0.823 | 0.070* |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | 62 | 0.088 | 0.048 | 0.067 | 0.136 | 179 | 724 | 2527 | 724 | 0.20 | 0.460 | 0.919 | 0.271 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | 62 | 0.126 | 0.113 | 0.080 | 0.189 | 179 | 785 | 2871 | 785 | 0.22 | 0.543 | 0.774 | 0.184* |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | 62 | 0.194 | 0.129 | 0.127 | 0.245 | 179 | 1132 | 1548 | 1132 | 0.24 | 0.511 | 0.903 | 0.198 |
| Laya 421M yes/no per pair (self-hosted) | 62 | 0.164 | 0.065 | 0.124 | 0.202 | 179 | 144 | 275 | 144 | 0.03 | 0.492 | 0.903 | 0.510 |
| Laya 421M 4-level rubric per pair (self-hosted) | 62 | 0.149 | 0.097 | 0.113 | 0.196 | 179 | 144 | 276 | 144 | 0.03 | 0.495 | 0.903 | 0.523* |
| Laya multilingual 322M yes/no per pair (self-hosted) | 62 | 0.172 | 0.097 | 0.117 | 0.239 | 179 | 150 | 273 | 150 | 0.03 | 0.496 | 0.903 | 0.587 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | 62 | 0.170 | 0.097 | 0.100 | 0.242 | 179 | 412 | 1170 | 412 | 0.11 | 0.517 | 0.887 | 0.325 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | 62 | 0.192 | 0.097 | 0.123 | 0.265 | 179 | 795 | 2288 | 795 | 0.21 | 0.507 | 0.903 | 0.171 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | 62 | 0.187 | 0.145 | 0.124 | 0.285 | 179 | 1368 | 3212 | 1368 | 0.35 | 0.509 | 0.903 | 0.100 |
| Open-Jev 2B yes/no per pair (self-hosted) | 62 | 0.224 | 0.145 | 0.159 | 0.293 | 5370 | 600 | 831 | 17970 | 0.59 | 0.517 | 0.903 | 0.058 |
| Open-Jev 9B yes/no per pair (self-hosted) | 62 | 0.302 | 0.274 | 0.258 | 0.423 | 5370 | 861 | 2377 | 25603 | 2.66 | 0.557 | 0.887 | 0.073 |
| Qwen3-Reranker-4B (self-hosted) | 62 | 0.334 | 0.290 | 0.296 | 0.468 | 179 | 4144 | 7429 | 4144 | 0.39 | 0.542 | 0.806 | — |
| bge-reranker-v2-m3 (self-hosted) | 62 | 0.234 | 0.161 | 0.165 | 0.310 | 179 | 1908 | 3488 | 1908 | 0.17 | 0.515 | 0.871 | — |
| mxbai-rerank-base-v2 (self-hosted) | 62 | 0.296 | 0.226 | 0.259 | 0.377 | 179 | 2238 | 4210 | 2238 | 0.20 | 0.537 | 0.887 | — |
| Qwen3.5-4B yes/no per pair (self-hosted) | 62 | 0.352 | 0.339 | 0.288 | 0.498 | 179 | 4206 | 7277 | 4206 | 0.36 | 0.591 | 0.839 | 0.060 |
| tev1-4B relevant / not per pair (self-hosted) | 62 | 0.322 | 0.290 | 0.240 | 0.441 | 179 | 4946 | 8220 | 4946 | 0.42 | 0.585 | 0.839 | 0.067 |
| reflex 4B yes/no per pair (self-hosted) | 62 | 0.308 | 0.274 | 0.251 | 0.437 | 5370 | 407 | 548 | 12050 | 0.47 | 0.580 | 0.855 | 0.050 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | 62 | 0.346 | 0.323 | 0.270 | 0.497 | 5370 | 917 | 1322 | 27809 | 1.09 | 0.572 | 0.855 | 0.109 |
| decider-2b v11 yes/no per pair (self-hosted) | 62 | 0.321 | 0.339 | 0.271 | 0.470 | 5370 | 2341 | 4449 | 73359 | 0.18 | 0.561 | 0.871 | 0.216 |

Jev Choice's own nothing-relevant signals (bright-stackoverflow):

| signal | AUROC | false accept @90% | median with answer | median without |
|---|---|---|---|---|
| max_score | 0.538 | 0.871 | 0.465 | 0.450 |
| 1-P(none) | 0.594 | 0.855 | 0.840 | 0.780 |
| P(any) | 0.587 | 0.855 | 0.690 | 0.610 |

TypeSafe's confidence bands on real data, Jev one Choice + none (bright-stackoverflow), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 28 | 0.321 | 0.357 |
| 0.5-0.9 | 27 | 0.333 | 0.185 |
| >=0.9 | 7 | 0.714 | 0.000 |

TypeSafe's confidence bands on real data, Jev tournament (6 groups, then final) (bright-stackoverflow), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 28 | 0.286 | 0.000 |
| 0.5-0.9 | 25 | 0.360 | 0.000 |
| >=0.9 | 9 | 0.556 | 0.000 |

Position bias (bright-stackoverflow): the same 30 passages sent in reverse order to Jev Choice. Same top pick 68% of the time (n=62); nDCG@10 0.371 normal vs 0.394 reversed; mean probability shift per passage 0.016; P(none) shift 0.048.

## bright-sustainable_living

108 queries; 47 have an answer in BM25's top 30 and are scored.

| Model | n | nDCG@10 | Top-1 | Recall@5 | MRR@10 | calls | median ms/call | p95 ms/call | median ms/query | $ per 1k queries | none-test AUROC | false accept @90% | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BM25 (floor) | 47 | 0.193 | 0.170 | 0.165 | 0.273 | 0 | — | — | 0 | 0.00 | 0.505 | 0.894 | — |
| Cohere Rerank 4 Pro | 47 | 0.447 | 0.489 | 0.379 | 0.648 | 155 | 958 | 1685 | 1380 | 2.50 | 0.599 | 0.809 | 0.470* |
| Cohere Rerank 4 Fast | 47 | 0.445 | 0.511 | 0.390 | 0.658 | 155 | 617 | 1371 | 674 | 2.00 | 0.604 | 0.787 | 0.382* |
| ZeroEntropy zerank-2 | 47 | 0.490 | 0.617 | 0.434 | 0.733 | 155 | 2225 | 3189 | 2325 | 0.21 | 0.623 | 0.723 | 0.221* |
| DeepSeek V4.1 Flash P(yes) per pair | 47 | 0.306 | 0.319 | 0.281 | 0.448 | 4650 | 1057 | 1416 | 32769 | 1.20 | 0.564 | 1.000 | 0.085 |
| DeepSeek V4.1 Flash JSON, 30 in one call | 47 | 0.508 | 0.596 | 0.413 | 0.722 | 155 | 2029 | 4166 | 2030 | 0.73 | 0.644 | 0.830 | 0.050* |
| Jev yes/no per pair | 47 | 0.487 | 0.617 | 0.435 | 0.731 | 4650 | 270 | 371 | 8693 | 0.79 | 0.670 | 0.638 | 0.037 |
| Jev 30 yes/no in one call | 47 | 0.503 | 0.596 | 0.427 | 0.738 | 155 | 470 | 1406 | 471 | 0.29 | 0.665 | 0.702 | 0.045 |
| Jev one Choice + none | 47 | 0.459 | 0.553 | 0.392 | 0.710 | 155 | 447 | 22372 | 448 | 0.21 | 0.647 | 0.766 | 0.048* |
| Jev 4-level rubric, 30 in one call | 47 | 0.510 | 0.660 | 0.433 | 0.780 | 155 | 331 | 22051 | 331 | 0.32 | 0.669 | 0.681 | 0.228* |
| Jev 45 duels in one call (top 10) | 47 | 0.291 | 0.426 | 0.247 | 0.507 | 155 | 286 | 2401 | 287 | 0.17 | 0.600 | 0.830 | — |
| Jev tournament (6 groups, then final) | 47 | 0.481 | 0.617 | 0.384 | 0.751 | 310 | 280 | 21991 | 588 | 0.29 | 0.642 | 0.681 | — |
| Jev cascade (batch prune, then 8 pairs) | 47 | 0.503 | 0.638 | 0.434 | 0.753 | 1395 | 274 | 464 | 2606 | 0.51 | 0.663 | 0.638 | — |
| Jev one Choice, passages reversed | 47 | 0.472 | 0.574 | 0.403 | 0.734 | 155 | 302 | 1193 | 302 | 0.21 | 0.648 | 0.702 | 0.045* |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | 47 | 0.131 | 0.043 | 0.125 | 0.195 | 155 | 217 | 335 | 217 | 0.05 | 0.555 | 0.872 | 0.168 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | 47 | 0.206 | 0.170 | 0.159 | 0.299 | 155 | 269 | 393 | 269 | 0.06 | 0.520 | 0.936 | 0.155* |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | 47 | 0.164 | 0.128 | 0.145 | 0.231 | 155 | 726 | 1343 | 726 | 0.18 | 0.520 | 0.872 | 0.188 |
| Laya 421M yes/no per pair (self-hosted) | 47 | 0.267 | 0.128 | 0.234 | 0.336 | 155 | 144 | 272 | 144 | 0.03 | 0.519 | 0.851 | 0.314 |
| Laya 421M 4-level rubric per pair (self-hosted) | 47 | 0.266 | 0.191 | 0.245 | 0.367 | 155 | 144 | 272 | 144 | 0.03 | 0.537 | 0.872 | 0.426* |
| Laya multilingual 322M yes/no per pair (self-hosted) | 47 | 0.225 | 0.191 | 0.202 | 0.305 | 155 | 109 | 235 | 109 | 0.02 | 0.520 | 0.894 | 0.434 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | 47 | 0.149 | 0.085 | 0.129 | 0.178 | 155 | 191 | 420 | 191 | 0.04 | 0.509 | 0.872 | 0.547 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | 47 | 0.149 | 0.149 | 0.104 | 0.207 | 155 | 372 | 877 | 372 | 0.08 | 0.513 | 0.894 | 0.520 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | 47 | 0.189 | 0.128 | 0.175 | 0.232 | 155 | 559 | 1429 | 559 | 0.12 | 0.519 | 0.851 | 0.323 |
| Open-Jev 2B yes/no per pair (self-hosted) | 47 | 0.215 | 0.149 | 0.191 | 0.292 | 4650 | 391 | 473 | 11722 | 0.36 | 0.530 | 0.851 | 0.112 |
| Open-Jev 9B yes/no per pair (self-hosted) | 47 | 0.413 | 0.426 | 0.354 | 0.599 | 4650 | 541 | 1071 | 16209 | 1.62 | 0.602 | 0.809 | 0.074 |
| Qwen3-Reranker-4B (self-hosted) | 47 | 0.401 | 0.404 | 0.338 | 0.534 | 155 | 2702 | 3775 | 2702 | 0.20 | 0.570 | 0.851 | — |
| bge-reranker-v2-m3 (self-hosted) | 47 | 0.323 | 0.340 | 0.308 | 0.444 | 155 | 1049 | 1779 | 1049 | 0.08 | 0.563 | 0.830 | — |
| mxbai-rerank-base-v2 (self-hosted) | 47 | 0.338 | 0.234 | 0.318 | 0.416 | 155 | 1421 | 2016 | 1421 | 0.11 | 0.563 | 0.872 | — |
| Qwen3.5-4B yes/no per pair (self-hosted) | 47 | 0.415 | 0.511 | 0.362 | 0.614 | 155 | 2109 | 3287 | 2109 | 0.17 | 0.654 | 0.766 | 0.045 |
| tev1-4B relevant / not per pair (self-hosted) | 47 | 0.407 | 0.426 | 0.371 | 0.578 | 155 | 2487 | 3771 | 2487 | 0.20 | 0.587 | 0.830 | 0.065 |
| reflex 4B yes/no per pair (self-hosted) | 47 | 0.451 | 0.447 | 0.401 | 0.601 | 4650 | 328 | 384 | 9843 | 0.37 | 0.627 | 0.830 | 0.030 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | 47 | 0.463 | 0.532 | 0.404 | 0.690 | 4650 | 410 | 632 | 12452 | 0.48 | 0.623 | 0.787 | 0.075 |
| decider-2b v11 yes/no per pair (self-hosted) | 47 | 0.487 | 0.553 | 0.381 | 0.669 | 4650 | 1035 | 1842 | 31462 | 0.08 | 0.636 | 0.766 | 0.119 |

Jev Choice's own nothing-relevant signals (bright-sustainable_living):

| signal | AUROC | false accept @90% | median with answer | median without |
|---|---|---|---|---|
| max_score | 0.647 | 0.766 | 0.560 | 0.350 |
| 1-P(none) | 0.663 | 0.723 | 0.860 | 0.680 |
| P(any) | 0.662 | 0.745 | 0.760 | 0.510 |

TypeSafe's confidence bands on real data, Jev one Choice + none (bright-sustainable_living), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 15 | 0.467 | 0.200 |
| 0.5-0.9 | 24 | 0.500 | 0.250 |
| >=0.9 | 8 | 0.875 | 0.000 |

TypeSafe's confidence bands on real data, Jev tournament (6 groups, then final) (bright-sustainable_living), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 19 | 0.526 | 0.000 |
| 0.5-0.9 | 19 | 0.579 | 0.000 |
| >=0.9 | 9 | 0.889 | 0.000 |

Position bias (bright-sustainable_living): the same 30 passages sent in reverse order to Jev Choice. Same top pick 72% of the time (n=47); nDCG@10 0.459 normal vs 0.472 reversed; mean probability shift per passage 0.011; P(none) shift 0.040.

## csn-python

300 queries; 256 have an answer in BM25's top 30 and are scored.

| Model | n | nDCG@10 | Top-1 | Recall@5 | MRR@10 | calls | median ms/call | p95 ms/call | median ms/query | $ per 1k queries | none-test AUROC | false accept @90% | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BM25 (floor) | 256 | 0.717 | 0.559 | 0.801 | 0.662 | 0 | — | — | 0 | 0.00 | 0.561 | 0.844 | — |
| Cohere Rerank 4 Pro | 256 | 0.982 | 0.957 | 1.000 | 0.976 | 556 | 854 | 1574 | 929 | 2.57 | 0.950 | 0.145 | 0.341* |
| Cohere Rerank 4 Fast | 256 | 0.971 | 0.930 | 1.000 | 0.962 | 556 | 878 | 1788 | 929 | 2.05 | 0.913 | 0.254 | 0.286* |
| ZeroEntropy zerank-2 | 256 | 0.963 | 0.910 | 1.000 | 0.950 | 556 | 2413 | 3476 | 2727 | 0.26 | 0.902 | 0.230 | 0.207* |
| DeepSeek V4.1 Flash P(yes) per pair | 256 | 0.921 | 0.828 | 0.980 | 0.898 | 16680 | 1052 | 1757 | 34224 | 1.69 | 0.805 | 0.371 | 0.021 |
| DeepSeek V4.1 Flash JSON, 30 in one call | 256 | 0.956 | 0.926 | 0.973 | 0.946 | 556 | 1927 | 2985 | 1927 | 1.32 | 0.925 | 0.156 | 0.013* |
| Jev yes/no per pair | 256 | 0.965 | 0.918 | 0.992 | 0.953 | 16680 | 256 | 322 | 7952 | 0.92 | 0.889 | 0.242 | 0.072 |
| Jev 30 yes/no in one call | 256 | 0.980 | 0.953 | 0.996 | 0.973 | 556 | 326 | 669 | 335 | 0.44 | 0.925 | 0.219 | 0.058 |
| Jev one Choice + none | 256 | 0.983 | 0.965 | 0.992 | 0.978 | 556 | 347 | 757 | 349 | 0.35 | 0.928 | 0.172 | 0.002* |
| Jev 4-level rubric, 30 in one call | 256 | 0.983 | 0.957 | 1.000 | 0.977 | 556 | 338 | 810 | 343 | 0.47 | 0.927 | 0.176 | 0.135* |
| Jev 45 duels in one call (top 10) | 256 | 0.881 | 0.867 | 0.891 | 0.878 | 556 | 311 | 540 | 311 | 0.22 | 0.857 | 0.352 | — |
| Jev tournament (6 groups, then final) | 256 | 0.977 | 0.957 | 0.977 | 0.970 | 1112 | 299 | 549 | 629 | 0.45 | 0.938 | 0.172 | — |
| Jev cascade (batch prune, then 8 pairs) | 256 | 0.968 | 0.926 | 0.992 | 0.957 | 5004 | 261 | 338 | 2445 | 0.68 | 0.896 | 0.227 | — |
| Jev one Choice, passages reversed | 256 | 0.982 | 0.961 | 0.996 | 0.977 | 300 | 316 | 646 | 317 | 0.35 | — | — | 0.002* |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | 256 | 0.133 | 0.043 | 0.160 | 0.097 | 556 | 376 | 593 | 376 | 0.09 | 0.475 | 0.887 | 0.387 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | 256 | 0.445 | 0.199 | 0.559 | 0.353 | 556 | 436 | 645 | 436 | 0.10 | 0.521 | 0.887 | 0.354* |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | 256 | 0.706 | 0.465 | 0.844 | 0.629 | 556 | 797 | 1384 | 797 | 0.19 | 0.572 | 0.844 | 0.183 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | 256 | 0.431 | 0.172 | 0.523 | 0.328 | 300 | 367 | 563 | 367 | 0.08 | — | — | 0.395* |
| Laya 421M yes/no per pair (self-hosted) | 256 | 0.585 | 0.348 | 0.703 | 0.501 | 556 | 144 | 275 | 144 | 0.03 | 0.555 | 0.812 | 0.504 |
| Laya 421M 4-level rubric per pair (self-hosted) | 256 | 0.620 | 0.387 | 0.738 | 0.541 | 556 | 144 | 275 | 144 | 0.03 | 0.575 | 0.801 | 0.558* |
| Laya multilingual 322M yes/no per pair (self-hosted) | 256 | 0.288 | 0.117 | 0.379 | 0.221 | 556 | 150 | 268 | 150 | 0.03 | 0.513 | 0.891 | 0.609 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | 256 | 0.473 | 0.273 | 0.559 | 0.397 | 556 | 224 | 570 | 224 | 0.06 | 0.561 | 0.863 | 0.211 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | 256 | 0.550 | 0.355 | 0.629 | 0.483 | 556 | 453 | 1265 | 453 | 0.12 | 0.570 | 0.852 | 0.234 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | 256 | 0.520 | 0.320 | 0.598 | 0.443 | 556 | 781 | 2363 | 781 | 0.20 | 0.556 | 0.875 | 0.058 |
| Open-Jev 2B yes/no per pair (self-hosted) | 256 | 0.860 | 0.727 | 0.949 | 0.820 | 16680 | 430 | 668 | 12935 | 0.42 | 0.740 | 0.609 | 0.094 |
| Open-Jev 9B yes/no per pair (self-hosted) | 256 | 0.893 | 0.789 | 0.965 | 0.863 | 16680 | 642 | 1201 | 19444 | 2.05 | 0.822 | 0.414 | 0.010 |
| Qwen3-Reranker-4B (self-hosted) | 256 | 0.976 | 0.941 | 0.996 | 0.967 | 556 | 2681 | 5242 | 2681 | 0.24 | 0.944 | 0.184 | — |
| bge-reranker-v2-m3 (self-hosted) | 256 | 0.835 | 0.695 | 0.918 | 0.793 | 556 | 1284 | 2541 | 1284 | 0.11 | 0.683 | 0.723 | — |
| mxbai-rerank-base-v2 (self-hosted) | 256 | 0.971 | 0.930 | 1.000 | 0.961 | 556 | 1440 | 2848 | 1440 | 0.13 | 0.849 | 0.414 | — |
| Qwen3.5-4B yes/no per pair (self-hosted) | 256 | 0.954 | 0.898 | 0.992 | 0.940 | 556 | 2461 | 4784 | 2461 | 0.21 | 0.879 | 0.320 | 0.031 |
| tev1-4B relevant / not per pair (self-hosted) | 256 | 0.942 | 0.863 | 0.996 | 0.922 | 556 | 2909 | 5455 | 2909 | 0.25 | 0.849 | 0.328 | 0.125 |
| reflex 4B yes/no per pair (self-hosted) | 256 | 0.922 | 0.824 | 0.992 | 0.897 | 16680 | 351 | 512 | 10397 | 0.41 | 0.824 | 0.402 | 0.136 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | 256 | 0.954 | 0.902 | 0.992 | 0.941 | 16680 | 538 | 1148 | 15881 | 0.66 | 0.862 | 0.355 | 0.047 |
| decider-2b v11 yes/no per pair (self-hosted) | 256 | 0.914 | 0.820 | 0.977 | 0.889 | 16680 | 1375 | 2528 | 41854 | 0.10 | 0.822 | 0.488 | 0.225 |

Jev Choice's own nothing-relevant signals (csn-python):

| signal | AUROC | false accept @90% | median with answer | median without |
|---|---|---|---|---|
| max_score | 0.928 | 0.172 | 0.970 | 0.290 |
| 1-P(none) | 0.927 | 0.215 | 0.980 | 0.480 |
| P(any) | 0.921 | 0.230 | 0.910 | 0.400 |

TypeSafe's confidence bands on real data, Jev one Choice + none (csn-python), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 14 | 0.786 | 0.143 |
| 0.5-0.9 | 66 | 0.924 | 0.015 |
| >=0.9 | 176 | 0.994 | 0.000 |

TypeSafe's confidence bands on real data, Jev tournament (6 groups, then final) (csn-python), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 8 | 0.875 | 0.000 |
| 0.5-0.9 | 56 | 0.893 | 0.000 |
| >=0.9 | 192 | 0.979 | 0.000 |

Position bias (csn-python): the same 30 passages sent in reverse order to Jev Choice. Same top pick 97% of the time (n=256); nDCG@10 0.983 normal vs 0.982 reversed; mean probability shift per passage 0.004; P(none) shift 0.029.

## miracl-fr

269 queries; 152 have an answer in BM25's top 30 and are scored.

| Model | n | nDCG@10 | Top-1 | Recall@5 | MRR@10 | calls | median ms/call | p95 ms/call | median ms/query | $ per 1k queries | none-test AUROC | false accept @90% | ECE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| BM25 (floor) | 152 | 0.234 | 0.079 | 0.251 | 0.199 | 0 | — | — | 0 | 0.00 | 0.502 | 0.901 | — |
| Cohere Rerank 4 Pro | 152 | 0.764 | 0.783 | 0.782 | 0.867 | 421 | 654 | 1179 | 683 | 2.50 | 0.764 | 0.605 | 0.496* |
| Cohere Rerank 4 Fast | 152 | 0.723 | 0.664 | 0.758 | 0.793 | 421 | 566 | 1016 | 587 | 2.00 | 0.733 | 0.605 | 0.400* |
| ZeroEntropy zerank-2 | 152 | 0.728 | 0.711 | 0.737 | 0.815 | 421 | 622 | 2480 | 622 | 0.11 | 0.681 | 0.750 | 0.263* |
| DeepSeek V4.1 Flash P(yes) per pair | 152 | 0.529 | 0.408 | 0.575 | 0.552 | 12630 | 1061 | 1345 | 32677 | 0.84 | 0.549 | 0.829 | 0.146 |
| DeepSeek V4.1 Flash JSON, 30 in one call | 152 | 0.669 | 0.645 | 0.683 | 0.745 | 421 | 1829 | 2650 | 1829 | 0.68 | 0.708 | 0.625 | 0.111* |
| Jev yes/no per pair | 152 | 0.663 | 0.586 | 0.675 | 0.711 | 12630 | 258 | 331 | 7878 | 0.60 | 0.667 | 0.770 | 0.158 |
| Jev 30 yes/no in one call | 152 | 0.690 | 0.632 | 0.735 | 0.745 | 421 | 289 | 583 | 289 | 0.27 | 0.702 | 0.717 | 0.142 |
| Jev one Choice + none | 152 | 0.700 | 0.684 | 0.714 | 0.789 | 421 | 283 | 546 | 283 | 0.19 | 0.701 | 0.691 | 0.024* |
| Jev 4-level rubric, 30 in one call | 152 | 0.696 | 0.671 | 0.712 | 0.765 | 421 | 303 | 785 | 303 | 0.31 | 0.700 | 0.704 | 0.308* |
| Jev 45 duels in one call (top 10) | 152 | 0.410 | 0.454 | 0.395 | 0.498 | 421 | 279 | 474 | 279 | 0.15 | 0.636 | 0.882 | — |
| Jev tournament (6 groups, then final) | 152 | 0.689 | 0.651 | 0.689 | 0.774 | 842 | 281 | 461 | 570 | 0.26 | 0.673 | 0.691 | — |
| Jev cascade (batch prune, then 8 pairs) | 152 | 0.660 | 0.579 | 0.718 | 0.707 | 3789 | 285 | 381 | 2656 | 0.44 | 0.667 | 0.770 | — |
| Jev one Choice, passages reversed | 152 | 0.675 | 0.664 | 0.695 | 0.770 | 269 | 296 | 545 | 296 | 0.19 | — | — | 0.025* |
| Laya 421M yes/no per pair (self-hosted) | 152 | 0.474 | 0.336 | 0.496 | 0.485 | 421 | 141 | 268 | 141 | 0.03 | 0.571 | 0.816 | 0.254 |
| Laya 421M 4-level rubric per pair (self-hosted) | 152 | 0.443 | 0.309 | 0.449 | 0.455 | 421 | 142 | 269 | 142 | 0.03 | 0.587 | 0.836 | 0.375* |
| Laya multilingual 322M yes/no per pair (self-hosted) | 152 | 0.531 | 0.434 | 0.542 | 0.561 | 421 | 49 | 126 | 49 | 0.01 | 0.609 | 0.829 | 0.244 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | 152 | 0.328 | 0.164 | 0.366 | 0.316 | 421 | 110 | 198 | 110 | 0.02 | 0.512 | 0.888 | 0.608 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | 152 | 0.469 | 0.336 | 0.453 | 0.489 | 421 | 219 | 416 | 219 | 0.05 | 0.549 | 0.836 | 0.397 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | 152 | 0.419 | 0.224 | 0.460 | 0.401 | 421 | 262 | 511 | 262 | 0.06 | 0.547 | 0.842 | 0.565 |
| Open-Jev 2B yes/no per pair (self-hosted) | 152 | 0.558 | 0.447 | 0.600 | 0.581 | 12630 | 331 | 404 | 9945 | 0.31 | 0.594 | 0.809 | 0.215 |
| Open-Jev 9B yes/no per pair (self-hosted) | 152 | 0.628 | 0.513 | 0.657 | 0.667 | 12630 | 530 | 588 | 15950 | 1.93 | 0.631 | 0.763 | 0.041 |
| Qwen3-Reranker-4B (self-hosted) | 152 | 0.766 | 0.737 | 0.785 | 0.845 | 421 | 1561 | 2604 | 1561 | 0.12 | 0.768 | 0.592 | — |
| bge-reranker-v2-m3 (self-hosted) | 152 | 0.732 | 0.697 | 0.765 | 0.813 | 421 | 499 | 883 | 499 | 0.04 | 0.706 | 0.763 | — |
| mxbai-rerank-base-v2 (self-hosted) | 152 | 0.700 | 0.645 | 0.745 | 0.771 | 421 | 864 | 1393 | 864 | 0.07 | 0.666 | 0.776 | — |
| Qwen3.5-4B yes/no per pair (self-hosted) | 152 | 0.577 | 0.487 | 0.594 | 0.629 | 421 | 1845 | 1953 | 1845 | 0.14 | 0.632 | 0.763 | 0.186 |
| tev1-4B relevant / not per pair (self-hosted) | 152 | 0.637 | 0.546 | 0.680 | 0.690 | 421 | 1930 | 2159 | 1930 | 0.15 | 0.656 | 0.750 | 0.222 |
| reflex 4B yes/no per pair (self-hosted) | 152 | 0.596 | 0.500 | 0.615 | 0.637 | 12630 | 324 | 381 | 9751 | 0.36 | 0.635 | 0.816 | 0.139 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | 152 | 0.668 | 0.612 | 0.701 | 0.729 | 12630 | 285 | 379 | 8897 | 0.33 | 0.676 | 0.684 | 0.138 |
| decider-2b v11 yes/no per pair (self-hosted) | 152 | 0.624 | 0.507 | 0.657 | 0.657 | 12630 | 675 | 1002 | 20159 | 0.05 | 0.636 | 0.776 | 0.233 |

Jev Choice's own nothing-relevant signals (miracl-fr):

| signal | AUROC | false accept @90% | median with answer | median without |
|---|---|---|---|---|
| max_score | 0.701 | 0.691 | 0.820 | 0.550 |
| 1-P(none) | 0.705 | 0.691 | 0.980 | 0.920 |
| P(any) | 0.679 | 0.704 | 0.950 | 0.865 |

TypeSafe's confidence bands on real data, Jev one Choice + none (miracl-fr), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 29 | 0.345 | 0.172 |
| 0.5-0.9 | 61 | 0.623 | 0.082 |
| >=0.9 | 62 | 0.903 | 0.000 |

TypeSafe's confidence bands on real data, Jev tournament (6 groups, then final) (miracl-fr), queries that do have an answer in the 30:

| confidence | n | top pick is right | said none |
|---|---|---|---|
| <0.5 | 34 | 0.324 | 0.000 |
| 0.5-0.9 | 54 | 0.630 | 0.000 |
| >=0.9 | 64 | 0.844 | 0.000 |

Position bias (miracl-fr): the same 30 passages sent in reverse order to Jev Choice. Same top pick 81% of the time (n=152); nDCG@10 0.700 normal vs 0.675 reversed; mean probability shift per passage 0.012; P(none) shift 0.022.

ECE marked * is for scores the vendor does not present as probabilities (shown for completeness, not held against them).

## Usage totals (check these against each vendor's dashboard)

| Model | dataset | calls | usage | $ all variants |
|---|---|---|---|---|
| Cohere Rerank 4 Pro | scifact | 564 | search_units=564 | 1.4100 |
| Cohere Rerank 4 Fast | scifact | 564 | search_units=564 | 1.1280 |
| ZeroEntropy zerank-2 | scifact | 564 | total_tokens=6164440, total_bytes=29441718, inference_latency_s=233.48 | 0.1541 |
| DeepSeek V4.1 Flash P(yes) per pair | scifact | 16920 | prompt_tokens=6371684, completion_tokens=16920, total_tokens=6388604, cost=0.76, is_byok=0 | 0.7572 |
| DeepSeek V4.1 Flash JSON, 30 in one call | scifact | 564 | prompt_tokens=5269193, completion_tokens=118440, total_tokens=5387633, cost=0.84, is_byok=0 | 0.8420 |
| Jev yes/no per pair | scifact | 16920 | input_tokens=12088213, output_tokens=372240 | 0.5077 |
| Jev 30 yes/no in one call | scifact | 564 | input_tokens=7468237, output_tokens=306816 | 0.3137 |
| Jev one Choice + none | scifact | 564 | input_tokens=6379717, output_tokens=175944 | 0.2679 |
| Jev 4-level rubric, 30 in one call | scifact | 564 | input_tokens=7941997, output_tokens=256056 | 0.3336 |
| Jev 45 duels in one call (top 10) | scifact | 564 | input_tokens=3412087, output_tokens=991512 | 0.1433 |
| Jev tournament (6 groups, then final) | scifact | 1128 | input_tokens=8071107, output_tokens=283390 | 0.3390 |
| Jev cascade (batch prune, then 8 pairs) | scifact | 5076 | input_tokens=10712731, output_tokens=406080 | 0.4499 |
| Jev one Choice, passages reversed | scifact | 300 | input_tokens=3388110, output_tokens=93740 | 0.1423 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | scifact | 564 | gpu_ms=369534.59 | 0.0760 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | scifact | 564 | gpu_ms=353721.67 | 0.0727 |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | scifact | 564 | gpu_ms=601888.55 | 0.1237 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | scifact | 300 | gpu_ms=188155.14 | 0.0387 |
| Laya 421M yes/no per pair (self-hosted) | scifact | 564 | gpu_ms=112301.45 | 0.0210 |
| Laya 421M 4-level rubric per pair (self-hosted) | scifact | 564 | gpu_ms=100081.53 | 0.0186 |
| Laya multilingual 322M yes/no per pair (self-hosted) | scifact | 564 | gpu_ms=56169.95 | 0.0104 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | scifact | 564 | gpu_ms=116476.24 | 0.0223 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | scifact | 564 | gpu_ms=186707.56 | 0.0353 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | scifact | 564 | gpu_ms=308132.68 | 0.0583 |
| Open-Jev 2B yes/no per pair (self-hosted) | scifact | 16920 | input_tokens=7658271, output_tokens=0 | 0.1823 |
| Open-Jev 9B yes/no per pair (self-hosted) | scifact | 16920 | input_tokens=7658271, output_tokens=0 | 1.0354 |
| Qwen3-Reranker-4B (self-hosted) | scifact | 564 | gpu_ms=1405524.86 | 0.1054 |
| bge-reranker-v2-m3 (self-hosted) | scifact | 564 | gpu_ms=570861.39 | 0.0428 |
| mxbai-rerank-base-v2 (self-hosted) | scifact | 564 | gpu_ms=767587.37 | 0.0576 |
| Qwen3.5-4B yes/no per pair (self-hosted) | scifact | 564 | gpu_ms=1440747.11 | 0.1081 |
| tev1-4B relevant / not per pair (self-hosted) | scifact | 564 | gpu_ms=1730429.47 | 0.1298 |
| reflex 4B yes/no per pair (self-hosted) | scifact | 16920 | input_tokens=10061982, output_tokens=0, state_tokens=7050222, question_tokens=3011760, state_cache_hit=0, images=0 | 0.2203 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | scifact | 16920 | input_tokens=8087551, output_tokens=0 | 0.2976 |
| decider-2b v11 yes/no per pair (self-hosted) | scifact | 16920 | input_tokens=7368836, output_tokens=0 | 0.0504 |
| Cohere Rerank 4 Pro | fiqa | 1059 | search_units=1059 | 2.6475 |
| Cohere Rerank 4 Fast | fiqa | 1059 | search_units=1059 | 2.1180 |
| ZeroEntropy zerank-2 | fiqa | 1059 | total_tokens=7564780, total_bytes=37031485, inference_latency_s=437.91 | 0.1891 |
| DeepSeek V4.1 Flash P(yes) per pair | fiqa | 31770 | prompt_tokens=8789444, completion_tokens=31770, total_tokens=8821214, cost=1.17, is_byok=0 | 1.1677 |
| DeepSeek V4.1 Flash JSON, 30 in one call | fiqa | 1059 | prompt_tokens=6856806, completion_tokens=222454, total_tokens=7079260, cost=1.1, is_byok=0 | 1.1000 |
| Jev yes/no per pair | fiqa | 31770 | input_tokens=18279982, output_tokens=698940 | 0.7678 |
| Jev 30 yes/no in one call | fiqa | 1059 | input_tokens=9822746, output_tokens=576096 | 0.4126 |
| Jev one Choice + none | fiqa | 1059 | input_tokens=7778876, output_tokens=331177 | 0.3267 |
| Jev 4-level rubric, 30 in one call | fiqa | 1059 | input_tokens=10712306, output_tokens=480786 | 0.4499 |
| Jev 45 duels in one call (top 10) | fiqa | 1059 | input_tokens=4973155, output_tokens=1861722 | 0.2089 |
| Jev tournament (6 groups, then final) | fiqa | 2118 | input_tokens=10252602, output_tokens=538302 | 0.4306 |
| Jev cascade (batch prune, then 8 pairs) | fiqa | 9531 | input_tokens=14982151, output_tokens=762480 | 0.6293 |
| Jev one Choice, passages reversed | fiqa | 648 | input_tokens=4758686, output_tokens=202680 | 0.1999 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | fiqa | 1059 | gpu_ms=359982.16 | 0.0740 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | fiqa | 1059 | gpu_ms=451262.72 | 0.0928 |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | fiqa | 1059 | gpu_ms=1004501.36 | 0.2065 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | fiqa | 648 | gpu_ms=221002.33 | 0.0454 |
| Laya 421M yes/no per pair (self-hosted) | fiqa | 1059 | gpu_ms=185610.85 | 0.0346 |
| Laya 421M 4-level rubric per pair (self-hosted) | fiqa | 1059 | gpu_ms=187708.88 | 0.0350 |
| Laya multilingual 322M yes/no per pair (self-hosted) | fiqa | 1059 | gpu_ms=99967.5 | 0.0186 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | fiqa | 1059 | gpu_ms=159693.33 | 0.0305 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | fiqa | 1059 | gpu_ms=319595.02 | 0.0606 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | fiqa | 1059 | gpu_ms=494756.92 | 0.0936 |
| Open-Jev 2B yes/no per pair (self-hosted) | fiqa | 31770 | input_tokens=10431382, output_tokens=0 | 0.3153 |
| Open-Jev 9B yes/no per pair (self-hosted) | fiqa | 31770 | input_tokens=10431382, output_tokens=0 | 1.5245 |
| Qwen3-Reranker-4B (self-hosted) | fiqa | 1059 | gpu_ms=2350805.38 | 0.1763 |
| bge-reranker-v2-m3 (self-hosted) | fiqa | 1059 | gpu_ms=901222.91 | 0.0676 |
| mxbai-rerank-base-v2 (self-hosted) | fiqa | 1059 | gpu_ms=1276967.36 | 0.0958 |
| Qwen3.5-4B yes/no per pair (self-hosted) | fiqa | 1059 | gpu_ms=2228521.12 | 0.1671 |
| tev1-4B relevant / not per pair (self-hosted) | fiqa | 1059 | gpu_ms=2539740.33 | 0.1905 |
| reflex 4B yes/no per pair (self-hosted) | fiqa | 31770 | input_tokens=14949643, output_tokens=0, state_tokens=9294583, question_tokens=5655060, state_cache_hit=2, images=0 | 0.3930 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | fiqa | 31770 | input_tokens=11964756, output_tokens=0 | 0.4568 |
| decider-2b v11 yes/no per pair (self-hosted) | fiqa | 31770 | input_tokens=9887433, output_tokens=0 | 0.0733 |
| Cohere Rerank 4 Pro | nq | 820 | search_units=820 | 2.0500 |
| Cohere Rerank 4 Fast | nq | 820 | search_units=820 | 1.6400 |
| ZeroEntropy zerank-2 | nq | 820 | total_tokens=3291835, total_bytes=16636101, inference_latency_s=364.15 | 0.0823 |
| DeepSeek V4.1 Flash P(yes) per pair | nq | 24600 | prompt_tokens=4227883, completion_tokens=24600, total_tokens=4252483, cost=0.63, is_byok=0 | 0.6278 |
| DeepSeek V4.1 Flash JSON, 30 in one call | nq | 820 | prompt_tokens=2784241, completion_tokens=172264, total_tokens=2956505, cost=0.5, is_byok=0 | 0.4951 |
| Jev yes/no per pair | nq | 24600 | input_tokens=11589807, output_tokens=541200 | 0.4868 |
| Jev 30 yes/no in one call | nq | 820 | input_tokens=5116130, output_tokens=446080 | 0.2149 |
| Jev one Choice + none | nq | 820 | input_tokens=3533530, output_tokens=256414 | 0.1484 |
| Jev 4-level rubric, 30 in one call | nq | 820 | input_tokens=5804930, output_tokens=372280 | 0.2438 |
| Jev 45 duels in one call (top 10) | nq | 820 | input_tokens=3010063, output_tokens=1441560 | 0.1264 |
| Jev tournament (6 groups, then final) | nq | 1640 | input_tokens=4886396, output_tokens=415384 | 0.2052 |
| Jev cascade (batch prune, then 8 pairs) | nq | 7380 | input_tokens=8335183, output_tokens=590400 | 0.3501 |
| Jev one Choice, passages reversed | nq | 500 | input_tokens=2150207, output_tokens=156370 | 0.0903 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | nq | 820 | gpu_ms=166383.49 | 0.0342 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | nq | 820 | gpu_ms=228697.65 | 0.0470 |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | nq | 820 | gpu_ms=763841.26 | 0.1570 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | nq | 500 | gpu_ms=98600.73 | 0.0203 |
| Laya 421M yes/no per pair (self-hosted) | nq | 820 | gpu_ms=102135.58 | 0.0190 |
| Laya 421M 4-level rubric per pair (self-hosted) | nq | 820 | gpu_ms=109607.12 | 0.0203 |
| Laya multilingual 322M yes/no per pair (self-hosted) | nq | 820 | gpu_ms=49902.4 | 0.0092 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | nq | 820 | gpu_ms=71065.33 | 0.0136 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | nq | 820 | gpu_ms=141128.73 | 0.0268 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | nq | 820 | gpu_ms=211671.81 | 0.0403 |
| Open-Jev 2B yes/no per pair (self-hosted) | nq | 24600 | input_tokens=5481913, output_tokens=0 | 0.2248 |
| Open-Jev 9B yes/no per pair (self-hosted) | nq | 24600 | input_tokens=5481913, output_tokens=0 | 0.9891 |
| Qwen3-Reranker-4B (self-hosted) | nq | 820 | gpu_ms=1190553.1 | 0.0893 |
| bge-reranker-v2-m3 (self-hosted) | nq | 820 | gpu_ms=430525.51 | 0.0323 |
| mxbai-rerank-base-v2 (self-hosted) | nq | 820 | gpu_ms=659566.1 | 0.0495 |
| Qwen3.5-4B yes/no per pair (self-hosted) | nq | 820 | gpu_ms=1476671.11 | 0.1108 |
| tev1-4B relevant / not per pair (self-hosted) | nq | 820 | gpu_ms=1595688.33 | 0.1197 |
| reflex 4B yes/no per pair (self-hosted) | nq | 24600 | input_tokens=8999097, output_tokens=0, state_tokens=4620297, question_tokens=4378800, state_cache_hit=34, images=0 | 0.2979 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | nq | 24600 | input_tokens=6576454, output_tokens=0 | 0.2698 |
| decider-2b v11 yes/no per pair (self-hosted) | nq | 24600 | input_tokens=5086675, output_tokens=0 | 0.0397 |
| Cohere Rerank 4 Pro | nfcorpus | 561 | search_units=561 | 1.4025 |
| Cohere Rerank 4 Fast | nfcorpus | 561 | search_units=561 | 1.1220 |
| ZeroEntropy zerank-2 | nfcorpus | 561 | total_tokens=6094994, total_bytes=29072565, inference_latency_s=278.06 | 0.1524 |
| DeepSeek V4.1 Flash P(yes) per pair | nfcorpus | 16830 | prompt_tokens=6405640, completion_tokens=16830, total_tokens=6422470, cost=0.8, is_byok=0 | 0.8039 |
| DeepSeek V4.1 Flash JSON, 30 in one call | nfcorpus | 561 | prompt_tokens=5510474, completion_tokens=117810, total_tokens=5628284, cost=0.87, is_byok=0 | 0.8748 |
| Jev yes/no per pair | nfcorpus | 16830 | input_tokens=11913246, output_tokens=370260 | 0.5004 |
| Jev 30 yes/no in one call | nfcorpus | 561 | input_tokens=7562795, output_tokens=305184 | 0.3176 |
| Jev one Choice + none | nfcorpus | 561 | input_tokens=6480065, output_tokens=175127 | 0.2722 |
| Jev 4-level rubric, 30 in one call | nfcorpus | 561 | input_tokens=8034035, output_tokens=254694 | 0.3374 |
| Jev 45 duels in one call (top 10) | nfcorpus | 561 | input_tokens=3361512, output_tokens=986238 | 0.1412 |
| Jev tournament (6 groups, then final) | nfcorpus | 1122 | input_tokens=8203257, output_tokens=283038 | 0.3445 |
| Jev cascade (batch prune, then 8 pairs) | nfcorpus | 5049 | input_tokens=10813409, output_tokens=403920 | 0.4542 |
| Jev one Choice, passages reversed | nfcorpus | 323 | input_tokens=3718188, output_tokens=100895 | 0.1562 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | nfcorpus | 561 | gpu_ms=329201.3 | 0.0677 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | nfcorpus | 561 | gpu_ms=367378.02 | 0.0755 |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | nfcorpus | 561 | gpu_ms=581615.49 | 0.1196 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | nfcorpus | 323 | gpu_ms=175817.7 | 0.0361 |
| Laya 421M yes/no per pair (self-hosted) | nfcorpus | 561 | gpu_ms=99786.15 | 0.0185 |
| Laya 421M 4-level rubric per pair (self-hosted) | nfcorpus | 561 | gpu_ms=100084.9 | 0.0186 |
| Laya multilingual 322M yes/no per pair (self-hosted) | nfcorpus | 561 | gpu_ms=56314.37 | 0.0105 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | nfcorpus | 561 | gpu_ms=89135.91 | 0.0170 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | nfcorpus | 561 | gpu_ms=176741.69 | 0.0334 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | nfcorpus | 561 | gpu_ms=291808.04 | 0.0551 |
| Open-Jev 2B yes/no per pair (self-hosted) | nfcorpus | 16830 | input_tokens=7588884, output_tokens=0 | 0.1821 |
| Open-Jev 9B yes/no per pair (self-hosted) | nfcorpus | 16830 | input_tokens=7588884, output_tokens=0 | 0.9427 |
| Qwen3-Reranker-4B (self-hosted) | nfcorpus | 561 | gpu_ms=1399328.46 | 0.1049 |
| bge-reranker-v2-m3 (self-hosted) | nfcorpus | 561 | gpu_ms=533592.74 | 0.0400 |
| mxbai-rerank-base-v2 (self-hosted) | nfcorpus | 561 | gpu_ms=762936.86 | 0.0572 |
| Qwen3.5-4B yes/no per pair (self-hosted) | nfcorpus | 561 | gpu_ms=1443855.74 | 0.1083 |
| tev1-4B relevant / not per pair (self-hosted) | nfcorpus | 561 | gpu_ms=1680801.88 | 0.1261 |
| reflex 4B yes/no per pair (self-hosted) | nfcorpus | 16830 | input_tokens=9993126, output_tokens=0, state_tokens=6997386, question_tokens=2995740, state_cache_hit=167, images=0 | 0.2119 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | nfcorpus | 16830 | input_tokens=8162474, output_tokens=0 | 0.2992 |
| decider-2b v11 yes/no per pair (self-hosted) | nfcorpus | 16830 | input_tokens=7314483, output_tokens=0 | 0.0503 |
| Cohere Rerank 4 Pro | trec-covid | 93 | search_units=93 | 0.2325 |
| Cohere Rerank 4 Fast | trec-covid | 93 | search_units=93 | 0.1860 |
| ZeroEntropy zerank-2 | trec-covid | 93 | total_tokens=757658, total_bytes=3879586, inference_latency_s=42.62 | 0.0189 |
| DeepSeek V4.1 Flash P(yes) per pair | trec-covid | 2790 | prompt_tokens=823912, completion_tokens=2790, total_tokens=826702, cost=0.12, is_byok=0 | 0.1158 |
| DeepSeek V4.1 Flash JSON, 30 in one call | trec-covid | 93 | prompt_tokens=652775, completion_tokens=19530, total_tokens=672305, cost=0.11, is_byok=0 | 0.1092 |
| Jev yes/no per pair | trec-covid | 2790 | input_tokens=1708982, output_tokens=61380 | 0.0718 |
| Jev 30 yes/no in one call | trec-covid | 93 | input_tokens=962466, output_tokens=50592 | 0.0404 |
| Jev one Choice + none | trec-covid | 93 | input_tokens=782976, output_tokens=29085 | 0.0329 |
| Jev 4-level rubric, 30 in one call | trec-covid | 93 | input_tokens=1040586, output_tokens=42222 | 0.0437 |
| Jev 45 duels in one call (top 10) | trec-covid | 93 | input_tokens=461524, output_tokens=163494 | 0.0194 |
| Jev tournament (6 groups, then final) | trec-covid | 186 | input_tokens=1018625, output_tokens=47410 | 0.0428 |
| Jev cascade (batch prune, then 8 pairs) | trec-covid | 837 | input_tokens=1448712, output_tokens=66960 | 0.0608 |
| Jev one Choice, passages reversed | trec-covid | 50 | input_tokens=430350, output_tokens=15644 | 0.0181 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | trec-covid | 93 | gpu_ms=37268.97 | 0.0077 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | trec-covid | 93 | gpu_ms=42676.6 | 0.0088 |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | trec-covid | 93 | gpu_ms=82926.41 | 0.0170 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | trec-covid | 50 | gpu_ms=19894.75 | 0.0041 |
| Laya 421M yes/no per pair (self-hosted) | trec-covid | 93 | gpu_ms=16035.42 | 0.0029 |
| Laya 421M 4-level rubric per pair (self-hosted) | trec-covid | 93 | gpu_ms=16323.95 | 0.0029 |
| Laya multilingual 322M yes/no per pair (self-hosted) | trec-covid | 93 | gpu_ms=7957.38 | 0.0014 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | trec-covid | 93 | gpu_ms=12820.12 | 0.0024 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | trec-covid | 93 | gpu_ms=25919.9 | 0.0048 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | trec-covid | 93 | gpu_ms=41042.46 | 0.0075 |
| Open-Jev 2B yes/no per pair (self-hosted) | trec-covid | 2790 | input_tokens=1000401, output_tokens=0 | 0.0246 |
| Open-Jev 9B yes/no per pair (self-hosted) | trec-covid | 2790 | input_tokens=1000401, output_tokens=0 | 0.1284 |
| Qwen3-Reranker-4B (self-hosted) | trec-covid | 93 | gpu_ms=203913.89 | 0.0153 |
| bge-reranker-v2-m3 (self-hosted) | trec-covid | 93 | gpu_ms=79341.9 | 0.0060 |
| mxbai-rerank-base-v2 (self-hosted) | trec-covid | 93 | gpu_ms=111716.65 | 0.0084 |
| Qwen3.5-4B yes/no per pair (self-hosted) | trec-covid | 93 | gpu_ms=206706.03 | 0.0155 |
| tev1-4B relevant / not per pair (self-hosted) | trec-covid | 93 | gpu_ms=237490.15 | 0.0178 |
| reflex 4B yes/no per pair (self-hosted) | trec-covid | 2790 | input_tokens=1397024, output_tokens=0, state_tokens=900404, question_tokens=496620, state_cache_hit=0, images=0 | 0.0348 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | trec-covid | 2790 | input_tokens=1108893, output_tokens=0 | 0.0418 |
| decider-2b v11 yes/no per pair (self-hosted) | trec-covid | 2790 | input_tokens=952960, output_tokens=0 | 0.0061 |
| Cohere Rerank 4 Pro | bright-biology | 142 | search_units=142 | 0.3550 |
| Cohere Rerank 4 Fast | bright-biology | 142 | search_units=142 | 0.2840 |
| ZeroEntropy zerank-2 | bright-biology | 142 | total_tokens=980428, total_bytes=4909820, inference_latency_s=55.62 | 0.0245 |
| DeepSeek V4.1 Flash P(yes) per pair | bright-biology | 4260 | prompt_tokens=1145566, completion_tokens=4260, total_tokens=1149826, cost=0.14, is_byok=0 | 0.1361 |
| DeepSeek V4.1 Flash JSON, 30 in one call | bright-biology | 142 | prompt_tokens=468333, completion_tokens=29820, total_tokens=498153, cost=0.08, is_byok=0 | 0.0831 |
| Jev yes/no per pair | bright-biology | 4260 | input_tokens=2428927, output_tokens=93720 | 0.1020 |
| Jev 30 yes/no in one call | bright-biology | 142 | input_tokens=865797, output_tokens=77248 | 0.0364 |
| Jev one Choice + none | bright-biology | 142 | input_tokens=591737, output_tokens=44342 | 0.0249 |
| Jev 4-level rubric, 30 in one call | bright-biology | 142 | input_tokens=985077, output_tokens=64468 | 0.0414 |
| Jev 45 duels in one call (top 10) | bright-biology | 142 | input_tokens=532378, output_tokens=249636 | 0.0224 |
| Jev tournament (6 groups, then final) | bright-biology | 284 | input_tokens=834373, output_tokens=71714 | 0.0350 |
| Jev cascade (batch prune, then 8 pairs) | bright-biology | 1278 | input_tokens=1532455, output_tokens=102240 | 0.0644 |
| Jev one Choice, passages reversed | bright-biology | 103 | input_tokens=429040, output_tokens=32167 | 0.0180 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | bright-biology | 142 | gpu_ms=27627.49 | 0.0057 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | bright-biology | 142 | gpu_ms=34884.69 | 0.0072 |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | bright-biology | 142 | gpu_ms=125021.61 | 0.0257 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | bright-biology | 103 | gpu_ms=19572.54 | 0.0040 |
| Laya 421M yes/no per pair (self-hosted) | bright-biology | 142 | gpu_ms=18700.56 | 0.0034 |
| Laya 421M 4-level rubric per pair (self-hosted) | bright-biology | 142 | gpu_ms=19819.88 | 0.0036 |
| Laya multilingual 322M yes/no per pair (self-hosted) | bright-biology | 142 | gpu_ms=9538.78 | 0.0018 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | bright-biology | 142 | gpu_ms=14300.84 | 0.0027 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | bright-biology | 142 | gpu_ms=28592.28 | 0.0054 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | bright-biology | 142 | gpu_ms=45385.54 | 0.0086 |
| Open-Jev 2B yes/no per pair (self-hosted) | bright-biology | 4260 | input_tokens=1380085, output_tokens=0 | 0.0406 |
| Open-Jev 9B yes/no per pair (self-hosted) | bright-biology | 4260 | input_tokens=1380085, output_tokens=0 | 0.1828 |
| Qwen3-Reranker-4B (self-hosted) | bright-biology | 142 | gpu_ms=224784.81 | 0.0169 |
| bge-reranker-v2-m3 (self-hosted) | bright-biology | 142 | gpu_ms=90495.06 | 0.0068 |
| mxbai-rerank-base-v2 (self-hosted) | bright-biology | 142 | gpu_ms=124862.08 | 0.0094 |
| Qwen3.5-4B yes/no per pair (self-hosted) | bright-biology | 142 | gpu_ms=290193.45 | 0.0218 |
| tev1-4B relevant / not per pair (self-hosted) | bright-biology | 142 | gpu_ms=332661.47 | 0.0249 |
| reflex 4B yes/no per pair (self-hosted) | bright-biology | 4260 | input_tokens=1985019, output_tokens=0, state_tokens=1226739, question_tokens=758280, state_cache_hit=375, images=0 | 0.0513 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | bright-biology | 4260 | input_tokens=1572019, output_tokens=0 | 0.0598 |
| decider-2b v11 yes/no per pair (self-hosted) | bright-biology | 4260 | input_tokens=1305032, output_tokens=0 | 0.0095 |
| Cohere Rerank 4 Pro | bright-economics | 141 | search_units=141 | 0.3525 |
| Cohere Rerank 4 Fast | bright-economics | 141 | search_units=141 | 0.2820 |
| ZeroEntropy zerank-2 | bright-economics | 141 | total_tokens=1585926, total_bytes=7216913, inference_latency_s=73.34 | 0.0396 |
| DeepSeek V4.1 Flash P(yes) per pair | bright-economics | 4230 | prompt_tokens=1725455, completion_tokens=4230, total_tokens=1729685, cost=0.19, is_byok=0 | 0.1905 |
| DeepSeek V4.1 Flash JSON, 30 in one call | bright-economics | 141 | prompt_tokens=855818, completion_tokens=29610, total_tokens=885428, cost=0.14, is_byok=0 | 0.1373 |
| Jev yes/no per pair | bright-economics | 4230 | input_tokens=3081712, output_tokens=93060 | 0.1294 |
| Jev 30 yes/no in one call | bright-economics | 141 | input_tokens=1280105, output_tokens=76704 | 0.0538 |
| Jev one Choice + none | bright-economics | 141 | input_tokens=1007975, output_tokens=44031 | 0.0423 |
| Jev 4-level rubric, 30 in one call | bright-economics | 141 | input_tokens=1398545, output_tokens=64014 | 0.0587 |
| Jev 45 duels in one call (top 10) | bright-economics | 141 | input_tokens=679370, output_tokens=247878 | 0.0285 |
| Jev tournament (6 groups, then final) | bright-economics | 282 | input_tokens=1358113, output_tokens=71300 | 0.0570 |
| Jev cascade (batch prune, then 8 pairs) | bright-economics | 1269 | input_tokens=2150753, output_tokens=101520 | 0.0903 |
| Jev one Choice, passages reversed | bright-economics | 103 | input_tokens=736010, output_tokens=32165 | 0.0309 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | bright-economics | 141 | gpu_ms=47148.26 | 0.0097 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | bright-economics | 141 | gpu_ms=54946.67 | 0.0113 |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | bright-economics | 141 | gpu_ms=130605.03 | 0.0268 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | bright-economics | 103 | gpu_ms=33628.81 | 0.0069 |
| Laya 421M yes/no per pair (self-hosted) | bright-economics | 141 | gpu_ms=24270.11 | 0.0046 |
| Laya 421M 4-level rubric per pair (self-hosted) | bright-economics | 141 | gpu_ms=24322.55 | 0.0046 |
| Laya multilingual 322M yes/no per pair (self-hosted) | bright-economics | 141 | gpu_ms=20056.04 | 0.0038 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | bright-economics | 141 | gpu_ms=36113.51 | 0.0070 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | bright-economics | 141 | gpu_ms=71410.13 | 0.0137 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | bright-economics | 141 | gpu_ms=118635.19 | 0.0226 |
| Open-Jev 2B yes/no per pair (self-hosted) | bright-economics | 4230 | input_tokens=2036376, output_tokens=0 | 0.0439 |
| Open-Jev 9B yes/no per pair (self-hosted) | bright-economics | 4230 | input_tokens=2036376, output_tokens=0 | 0.2229 |
| Qwen3-Reranker-4B (self-hosted) | bright-economics | 141 | gpu_ms=464246.29 | 0.0348 |
| bge-reranker-v2-m3 (self-hosted) | bright-economics | 141 | gpu_ms=187484.08 | 0.0141 |
| mxbai-rerank-base-v2 (self-hosted) | bright-economics | 141 | gpu_ms=249393.79 | 0.0187 |
| Qwen3.5-4B yes/no per pair (self-hosted) | bright-economics | 141 | gpu_ms=383887.71 | 0.0288 |
| tev1-4B relevant / not per pair (self-hosted) | bright-economics | 141 | gpu_ms=442491.36 | 0.0332 |
| reflex 4B yes/no per pair (self-hosted) | bright-economics | 4230 | input_tokens=2637537, output_tokens=0, state_tokens=1884597, question_tokens=752940, state_cache_hit=85, images=0 | 0.0550 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | bright-economics | 4230 | input_tokens=2258024, output_tokens=0 | 0.0815 |
| decider-2b v11 yes/no per pair (self-hosted) | bright-economics | 4230 | input_tokens=1963399, output_tokens=0 | 0.0131 |
| Cohere Rerank 4 Pro | bright-earth_science | 173 | search_units=173 | 0.4325 |
| Cohere Rerank 4 Fast | bright-earth_science | 173 | search_units=173 | 0.3460 |
| ZeroEntropy zerank-2 | bright-earth_science | 173 | total_tokens=1288797, total_bytes=6151682, inference_latency_s=59.79 | 0.0322 |
| DeepSeek V4.1 Flash P(yes) per pair | bright-earth_science | 5190 | prompt_tokens=1483861, completion_tokens=5190, total_tokens=1489051, cost=0.19, is_byok=0 | 0.1919 |
| DeepSeek V4.1 Flash JSON, 30 in one call | bright-earth_science | 173 | prompt_tokens=705715, completion_tokens=36330, total_tokens=742045, cost=0.12, is_byok=0 | 0.1201 |
| Jev yes/no per pair | bright-earth_science | 5190 | input_tokens=3073716, output_tokens=114180 | 0.1291 |
| Jev 30 yes/no in one call | bright-earth_science | 173 | input_tokens=1208629, output_tokens=94112 | 0.0508 |
| Jev one Choice + none | bright-earth_science | 173 | input_tokens=874739, output_tokens=54023 | 0.0367 |
| Jev 4-level rubric, 30 in one call | bright-earth_science | 173 | input_tokens=1353949, output_tokens=78542 | 0.0569 |
| Jev 45 duels in one call (top 10) | bright-earth_science | 173 | input_tokens=700941, output_tokens=304134 | 0.0294 |
| Jev tournament (6 groups, then final) | bright-earth_science | 346 | input_tokens=1211888, output_tokens=87410 | 0.0509 |
| Jev cascade (batch prune, then 8 pairs) | bright-earth_science | 1557 | input_tokens=2064033, output_tokens=124560 | 0.0867 |
| Jev one Choice, passages reversed | bright-earth_science | 173 | input_tokens=874739, output_tokens=54031 | 0.0367 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | bright-earth_science | 173 | gpu_ms=40337.71 | 0.0083 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | bright-earth_science | 173 | gpu_ms=49276.72 | 0.0101 |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | bright-earth_science | 173 | gpu_ms=151592.61 | 0.0312 |
| Laya 421M yes/no per pair (self-hosted) | bright-earth_science | 173 | gpu_ms=26642.94 | 0.0049 |
| Laya 421M 4-level rubric per pair (self-hosted) | bright-earth_science | 173 | gpu_ms=27126.01 | 0.0050 |
| Laya multilingual 322M yes/no per pair (self-hosted) | bright-earth_science | 173 | gpu_ms=17682.35 | 0.0033 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | bright-earth_science | 173 | gpu_ms=23883.54 | 0.0046 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | bright-earth_science | 173 | gpu_ms=47807.39 | 0.0092 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | bright-earth_science | 173 | gpu_ms=76033.12 | 0.0146 |
| Open-Jev 2B yes/no per pair (self-hosted) | bright-earth_science | 5190 | input_tokens=1819427, output_tokens=0 | 0.0499 |
| Open-Jev 9B yes/no per pair (self-hosted) | bright-earth_science | 5190 | input_tokens=1819427, output_tokens=0 | 0.2681 |
| Qwen3-Reranker-4B (self-hosted) | bright-earth_science | 173 | gpu_ms=352653.15 | 0.0264 |
| bge-reranker-v2-m3 (self-hosted) | bright-earth_science | 173 | gpu_ms=139783.8 | 0.0105 |
| mxbai-rerank-base-v2 (self-hosted) | bright-earth_science | 173 | gpu_ms=193896.14 | 0.0145 |
| Qwen3.5-4B yes/no per pair (self-hosted) | bright-earth_science | 173 | gpu_ms=357696.46 | 0.0268 |
| tev1-4B relevant / not per pair (self-hosted) | bright-earth_science | 173 | gpu_ms=423986.86 | 0.0318 |
| reflex 4B yes/no per pair (self-hosted) | bright-earth_science | 5190 | input_tokens=2556668, output_tokens=0, state_tokens=1632848, question_tokens=923820, state_cache_hit=92, images=0 | 0.0627 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | bright-earth_science | 5190 | input_tokens=2128009, output_tokens=0 | 0.0798 |
| decider-2b v11 yes/no per pair (self-hosted) | bright-earth_science | 5190 | input_tokens=1727264, output_tokens=0 | 0.0115 |
| Cohere Rerank 4 Pro | bright-psychology | 130 | search_units=130 | 0.3250 |
| Cohere Rerank 4 Fast | bright-psychology | 130 | search_units=130 | 0.2600 |
| ZeroEntropy zerank-2 | bright-psychology | 130 | total_tokens=1202021, total_bytes=5843241, inference_latency_s=58.89 | 0.0301 |
| DeepSeek V4.1 Flash P(yes) per pair | bright-psychology | 3900 | prompt_tokens=1351308, completion_tokens=3900, total_tokens=1355208, cost=0.16, is_byok=0 | 0.1603 |
| DeepSeek V4.1 Flash JSON, 30 in one call | bright-psychology | 130 | prompt_tokens=650717, completion_tokens=27300, total_tokens=678017, cost=0.11, is_byok=0 | 0.1085 |
| Jev yes/no per pair | bright-psychology | 3900 | input_tokens=2558237, output_tokens=85800 | 0.1074 |
| Jev 30 yes/no in one call | bright-psychology | 130 | input_tokens=1029178, output_tokens=70720 | 0.0432 |
| Jev one Choice + none | bright-psychology | 130 | input_tokens=778278, output_tokens=40570 | 0.0327 |
| Jev 4-level rubric, 30 in one call | bright-psychology | 130 | input_tokens=1138378, output_tokens=59020 | 0.0478 |
| Jev 45 duels in one call (top 10) | bright-psychology | 130 | input_tokens=559781, output_tokens=228540 | 0.0235 |
| Jev tournament (6 groups, then final) | bright-psychology | 260 | input_tokens=1072770, output_tokens=65516 | 0.0451 |
| Jev cascade (batch prune, then 8 pairs) | bright-psychology | 1170 | input_tokens=1763713, output_tokens=93600 | 0.0741 |
| Jev one Choice, passages reversed | bright-psychology | 130 | input_tokens=778278, output_tokens=40570 | 0.0327 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | bright-psychology | 130 | gpu_ms=35882.97 | 0.0074 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | bright-psychology | 130 | gpu_ms=42969.35 | 0.0088 |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | bright-psychology | 130 | gpu_ms=121439.98 | 0.0250 |
| Laya 421M yes/no per pair (self-hosted) | bright-psychology | 130 | gpu_ms=22340.28 | 0.0042 |
| Laya 421M 4-level rubric per pair (self-hosted) | bright-psychology | 130 | gpu_ms=22509.41 | 0.0042 |
| Laya multilingual 322M yes/no per pair (self-hosted) | bright-psychology | 130 | gpu_ms=15882.78 | 0.0030 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | bright-psychology | 130 | gpu_ms=26422.61 | 0.0051 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | bright-psychology | 130 | gpu_ms=53665.76 | 0.0103 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | bright-psychology | 130 | gpu_ms=88321.08 | 0.0170 |
| Open-Jev 2B yes/no per pair (self-hosted) | bright-psychology | 3900 | input_tokens=1587437, output_tokens=0 | 0.0397 |
| Open-Jev 9B yes/no per pair (self-hosted) | bright-psychology | 3900 | input_tokens=1587437, output_tokens=0 | 0.1948 |
| Qwen3-Reranker-4B (self-hosted) | bright-psychology | 130 | gpu_ms=360693.89 | 0.0271 |
| bge-reranker-v2-m3 (self-hosted) | bright-psychology | 130 | gpu_ms=153183.39 | 0.0115 |
| mxbai-rerank-base-v2 (self-hosted) | bright-psychology | 130 | gpu_ms=194614.51 | 0.0146 |
| Qwen3.5-4B yes/no per pair (self-hosted) | bright-psychology | 130 | gpu_ms=312257.77 | 0.0234 |
| tev1-4B relevant / not per pair (self-hosted) | bright-psychology | 130 | gpu_ms=359483.8 | 0.0270 |
| reflex 4B yes/no per pair (self-hosted) | bright-psychology | 3900 | input_tokens=2141467, output_tokens=0, state_tokens=1447267, question_tokens=694200, state_cache_hit=108, images=0 | 0.0488 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | bright-psychology | 3900 | input_tokens=1799670, output_tokens=0 | 0.0661 |
| decider-2b v11 yes/no per pair (self-hosted) | bright-psychology | 3900 | input_tokens=1520339, output_tokens=0 | 0.0103 |
| Cohere Rerank 4 Pro | bright-robotics | 136 | search_units=170 | 0.4250 |
| Cohere Rerank 4 Fast | bright-robotics | 136 | search_units=170 | 0.3400 |
| ZeroEntropy zerank-2 | bright-robotics | 136 | total_tokens=1875936, total_bytes=7735933, inference_latency_s=61.73 | 0.0469 |
| DeepSeek V4.1 Flash P(yes) per pair | bright-robotics | 4080 | prompt_tokens=3659168, completion_tokens=4080, total_tokens=3663248, cost=0.2, is_byok=0 | 0.1964 |
| DeepSeek V4.1 Flash JSON, 30 in one call | bright-robotics | 136 | prompt_tokens=842555, completion_tokens=28560, total_tokens=871115, cost=0.13, is_byok=0 | 0.1294 |
| Jev yes/no per pair | bright-robotics | 4080 | input_tokens=5079305, output_tokens=89760 | 0.2133 |
| Jev 30 yes/no in one call | bright-robotics | 136 | input_tokens=1228044, output_tokens=73984 | 0.0516 |
| Jev one Choice + none | bright-robotics | 136 | input_tokens=965564, output_tokens=42454 | 0.0406 |
| Jev 4-level rubric, 30 in one call | bright-robotics | 136 | input_tokens=1342284, output_tokens=61744 | 0.0564 |
| Jev 45 duels in one call (top 10) | bright-robotics | 136 | input_tokens=714343, output_tokens=239088 | 0.0300 |
| Jev tournament (6 groups, then final) | bright-robotics | 272 | input_tokens=1350015, output_tokens=68724 | 0.0567 |
| Jev cascade (batch prune, then 8 pairs) | bright-robotics | 1224 | input_tokens=2614882, output_tokens=97920 | 0.1098 |
| Jev one Choice, passages reversed | bright-robotics | 136 | input_tokens=965564, output_tokens=42480 | 0.0406 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | bright-robotics | 136 | gpu_ms=63674.35 | 0.0131 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | bright-robotics | 136 | gpu_ms=73474.49 | 0.0151 |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | bright-robotics | 136 | gpu_ms=173728.24 | 0.0357 |
| Laya 421M yes/no per pair (self-hosted) | bright-robotics | 136 | gpu_ms=23289.78 | 0.0044 |
| Laya 421M 4-level rubric per pair (self-hosted) | bright-robotics | 136 | gpu_ms=23401.49 | 0.0044 |
| Laya multilingual 322M yes/no per pair (self-hosted) | bright-robotics | 136 | gpu_ms=21236.98 | 0.0040 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | bright-robotics | 136 | gpu_ms=145567.7 | 0.0296 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | bright-robotics | 136 | gpu_ms=269913.0 | 0.0548 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | bright-robotics | 135 | gpu_ms=389945.1 | 0.0783 |
| Open-Jev 2B yes/no per pair (self-hosted) | bright-robotics | 4080 | input_tokens=4041558, output_tokens=0 | 0.0877 |
| Open-Jev 9B yes/no per pair (self-hosted) | bright-robotics | 4080 | input_tokens=4041558, output_tokens=0 | 0.3703 |
| Qwen3-Reranker-4B (self-hosted) | bright-robotics | 136 | gpu_ms=947632.14 | 0.0711 |
| bge-reranker-v2-m3 (self-hosted) | bright-robotics | 136 | gpu_ms=500465.79 | 0.0375 |
| mxbai-rerank-base-v2 (self-hosted) | bright-robotics | 136 | gpu_ms=513179.05 | 0.0385 |
| Qwen3.5-4B yes/no per pair (self-hosted) | bright-robotics | 136 | gpu_ms=700956.44 | 0.0526 |
| tev1-4B relevant / not per pair (self-hosted) | bright-robotics | 136 | gpu_ms=801346.11 | 0.0601 |
| reflex 4B yes/no per pair (self-hosted) | bright-robotics | 4080 | input_tokens=4621824, output_tokens=0, state_tokens=3895584, question_tokens=726240, state_cache_hit=236, images=0 | 0.0761 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | bright-robotics | 4080 | input_tokens=4920954, output_tokens=0 | 0.1663 |
| decider-2b v11 yes/no per pair (self-hosted) | bright-robotics | 4080 | input_tokens=3971506, output_tokens=0 | 0.0260 |
| Cohere Rerank 4 Pro | bright-stackoverflow | 179 | search_units=185 | 0.4625 |
| Cohere Rerank 4 Fast | bright-stackoverflow | 179 | search_units=185 | 0.3700 |
| ZeroEntropy zerank-2 | bright-stackoverflow | 179 | total_tokens=3861511, total_bytes=15232103, inference_latency_s=103.36 | 0.0965 |
| DeepSeek V4.1 Flash P(yes) per pair | bright-stackoverflow | 5370 | prompt_tokens=4299878, completion_tokens=5370, total_tokens=4305248, cost=0.36, is_byok=0 | 0.3637 |
| DeepSeek V4.1 Flash JSON, 30 in one call | bright-stackoverflow | 179 | prompt_tokens=2382662, completion_tokens=37622, total_tokens=2420284, cost=0.35, is_byok=0 | 0.3505 |
| Jev yes/no per pair | bright-stackoverflow | 5370 | input_tokens=6167646, output_tokens=118140 | 0.2590 |
| Jev 30 yes/no in one call | bright-stackoverflow | 179 | input_tokens=3008146, output_tokens=97376 | 0.1263 |
| Jev one Choice + none | bright-stackoverflow | 179 | input_tokens=2662676, output_tokens=55889 | 0.1118 |
| Jev 4-level rubric, 30 in one call | bright-stackoverflow | 179 | input_tokens=3158506, output_tokens=81266 | 0.1327 |
| Jev 45 duels in one call (top 10) | bright-stackoverflow | 179 | input_tokens=1322655, output_tokens=314682 | 0.0556 |
| Jev tournament (6 groups, then final) | bright-stackoverflow | 358 | input_tokens=3342151, output_tokens=90404 | 0.1404 |
| Jev cascade (batch prune, then 8 pairs) | bright-stackoverflow | 1611 | input_tokens=4622099, output_tokens=128880 | 0.1941 |
| Jev one Choice, passages reversed | bright-stackoverflow | 179 | input_tokens=2662676, output_tokens=55897 | 0.1118 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | bright-stackoverflow | 179 | gpu_ms=163157.89 | 0.0335 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | bright-stackoverflow | 179 | gpu_ms=181111.88 | 0.0372 |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | bright-stackoverflow | 179 | gpu_ms=203017.1 | 0.0417 |
| Laya 421M yes/no per pair (self-hosted) | bright-stackoverflow | 179 | gpu_ms=31770.2 | 0.0059 |
| Laya 421M 4-level rubric per pair (self-hosted) | bright-stackoverflow | 179 | gpu_ms=31807.61 | 0.0059 |
| Laya multilingual 322M yes/no per pair (self-hosted) | bright-stackoverflow | 179 | gpu_ms=32698.76 | 0.0061 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | bright-stackoverflow | 179 | gpu_ms=97427.4 | 0.0182 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | bright-stackoverflow | 179 | gpu_ms=191140.57 | 0.0354 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | bright-stackoverflow | 179 | gpu_ms=301940.78 | 0.0581 |
| Open-Jev 2B yes/no per pair (self-hosted) | bright-stackoverflow | 5370 | input_tokens=5006391, output_tokens=0 | 0.1024 |
| Open-Jev 9B yes/no per pair (self-hosted) | bright-stackoverflow | 5370 | input_tokens=5006391, output_tokens=0 | 0.4550 |
| Qwen3-Reranker-4B (self-hosted) | bright-stackoverflow | 179 | gpu_ms=889112.93 | 0.0667 |
| bge-reranker-v2-m3 (self-hosted) | bright-stackoverflow | 179 | gpu_ms=392182.87 | 0.0294 |
| mxbai-rerank-base-v2 (self-hosted) | bright-stackoverflow | 179 | gpu_ms=461512.24 | 0.0346 |
| Qwen3.5-4B yes/no per pair (self-hosted) | bright-stackoverflow | 179 | gpu_ms=832361.97 | 0.0624 |
| tev1-4B relevant / not per pair (self-hosted) | bright-stackoverflow | 179 | gpu_ms=961583.29 | 0.0721 |
| reflex 4B yes/no per pair (self-hosted) | bright-stackoverflow | 5370 | input_tokens=5770873, output_tokens=0, state_tokens=4815013, question_tokens=955860, state_cache_hit=445, images=0 | 0.0829 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | bright-stackoverflow | 5370 | input_tokens=5680890, output_tokens=0 | 0.1892 |
| decider-2b v11 yes/no per pair (self-hosted) | bright-stackoverflow | 5370 | input_tokens=4913132, output_tokens=0 | 0.0314 |
| Cohere Rerank 4 Pro | bright-sustainable_living | 155 | search_units=155 | 0.3875 |
| Cohere Rerank 4 Fast | bright-sustainable_living | 155 | search_units=155 | 0.3100 |
| ZeroEntropy zerank-2 | bright-sustainable_living | 155 | total_tokens=1300737, total_bytes=6287815, inference_latency_s=61.16 | 0.0325 |
| DeepSeek V4.1 Flash P(yes) per pair | bright-sustainable_living | 4650 | prompt_tokens=1481505, completion_tokens=4650, total_tokens=1486155, cost=0.17, is_byok=0 | 0.1716 |
| DeepSeek V4.1 Flash JSON, 30 in one call | bright-sustainable_living | 155 | prompt_tokens=621284, completion_tokens=32582, total_tokens=653866, cost=0.11, is_byok=0 | 0.1055 |
| Jev yes/no per pair | bright-sustainable_living | 4650 | input_tokens=2907105, output_tokens=102300 | 0.1221 |
| Jev 30 yes/no in one call | bright-sustainable_living | 155 | input_tokens=1061413, output_tokens=84320 | 0.0446 |
| Jev one Choice + none | bright-sustainable_living | 155 | input_tokens=762263, output_tokens=48377 | 0.0320 |
| Jev 4-level rubric, 30 in one call | bright-sustainable_living | 155 | input_tokens=1191613, output_tokens=70370 | 0.0500 |
| Jev 45 duels in one call (top 10) | bright-sustainable_living | 155 | input_tokens=626088, output_tokens=272490 | 0.0263 |
| Jev tournament (6 groups, then final) | bright-sustainable_living | 310 | input_tokens=1069471, output_tokens=78232 | 0.0449 |
| Jev cascade (batch prune, then 8 pairs) | bright-sustainable_living | 1395 | input_tokens=1890146, output_tokens=111600 | 0.0794 |
| Jev one Choice, passages reversed | bright-sustainable_living | 155 | input_tokens=762263, output_tokens=48395 | 0.0320 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | bright-sustainable_living | 155 | gpu_ms=35444.53 | 0.0073 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | bright-sustainable_living | 155 | gpu_ms=43736.94 | 0.0090 |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | bright-sustainable_living | 155 | gpu_ms=136264.39 | 0.0280 |
| Laya 421M yes/no per pair (self-hosted) | bright-sustainable_living | 155 | gpu_ms=26274.63 | 0.0049 |
| Laya 421M 4-level rubric per pair (self-hosted) | bright-sustainable_living | 155 | gpu_ms=26442.67 | 0.0049 |
| Laya multilingual 322M yes/no per pair (self-hosted) | bright-sustainable_living | 155 | gpu_ms=18174.49 | 0.0034 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | bright-sustainable_living | 155 | gpu_ms=36080.68 | 0.0067 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | bright-sustainable_living | 155 | gpu_ms=70333.34 | 0.0129 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | bright-sustainable_living | 155 | gpu_ms=99351.66 | 0.0188 |
| Open-Jev 2B yes/no per pair (self-hosted) | bright-sustainable_living | 4650 | input_tokens=1759228, output_tokens=0 | 0.0554 |
| Open-Jev 9B yes/no per pair (self-hosted) | bright-sustainable_living | 4650 | input_tokens=1759228, output_tokens=0 | 0.2528 |
| Qwen3-Reranker-4B (self-hosted) | bright-sustainable_living | 155 | gpu_ms=408503.59 | 0.0306 |
| bge-reranker-v2-m3 (self-hosted) | bright-sustainable_living | 155 | gpu_ms=173287.25 | 0.0130 |
| mxbai-rerank-base-v2 (self-hosted) | bright-sustainable_living | 155 | gpu_ms=220599.57 | 0.0165 |
| Qwen3.5-4B yes/no per pair (self-hosted) | bright-sustainable_living | 155 | gpu_ms=353013.57 | 0.0265 |
| tev1-4B relevant / not per pair (self-hosted) | bright-sustainable_living | 155 | gpu_ms=408029.14 | 0.0306 |
| reflex 4B yes/no per pair (self-hosted) | bright-sustainable_living | 4650 | input_tokens=2419496, output_tokens=0, state_tokens=1591796, question_tokens=827700, state_cache_hit=128, images=0 | 0.0568 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | bright-sustainable_living | 4650 | input_tokens=2000620, output_tokens=0 | 0.0748 |
| decider-2b v11 yes/no per pair (self-hosted) | bright-sustainable_living | 4650 | input_tokens=1678941, output_tokens=0 | 0.0115 |
| Cohere Rerank 4 Pro | csn-python | 556 | search_units=572 | 1.4300 |
| Cohere Rerank 4 Fast | csn-python | 556 | search_units=572 | 1.1440 |
| ZeroEntropy zerank-2 | csn-python | 556 | total_tokens=5884101, total_bytes=27796530, inference_latency_s=340.97 | 0.1471 |
| DeepSeek V4.1 Flash P(yes) per pair | csn-python | 16680 | prompt_tokens=7566051, completion_tokens=16680, total_tokens=7582731, cost=0.74, is_byok=0 | 0.7402 |
| DeepSeek V4.1 Flash JSON, 30 in one call | csn-python | 556 | prompt_tokens=4463054, completion_tokens=116760, total_tokens=4579814, cost=0.71, is_byok=0 | 0.7105 |
| Jev yes/no per pair | csn-python | 16680 | input_tokens=12372066, output_tokens=366960 | 0.5196 |
| Jev 30 yes/no in one call | csn-python | 556 | input_tokens=5798454, output_tokens=302464 | 0.2435 |
| Jev one Choice + none | csn-python | 556 | input_tokens=4725374, output_tokens=173662 | 0.1985 |
| Jev 4-level rubric, 30 in one call | csn-python | 556 | input_tokens=6265494, output_tokens=252424 | 0.2632 |
| Jev 45 duels in one call (top 10) | csn-python | 556 | input_tokens=2890448, output_tokens=977448 | 0.1214 |
| Jev tournament (6 groups, then final) | csn-python | 1112 | input_tokens=6076198, output_tokens=279998 | 0.2552 |
| Jev cascade (batch prune, then 8 pairs) | csn-python | 5004 | input_tokens=9084299, output_tokens=400320 | 0.3815 |
| Jev one Choice, passages reversed | csn-python | 300 | input_tokens=2529041, output_tokens=93838 | 0.1062 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys (self-hosted) | csn-python | 556 | gpu_ms=226652.43 | 0.0466 |
| Qwen2.5-1.5B RLCD, 30 rubric keys (self-hosted) | csn-python | 556 | gpu_ms=268217.67 | 0.0551 |
| Qwen2.5-1.5B RLCD, one passage per prompt (self-hosted) | csn-python | 556 | gpu_ms=530989.78 | 0.1091 |
| Qwen2.5-1.5B RLCD, 30 yes/no keys, passages reversed | csn-python | 300 | gpu_ms=114924.44 | 0.0236 |
| Laya 421M yes/no per pair (self-hosted) | csn-python | 556 | gpu_ms=98533.63 | 0.0183 |
| Laya 421M 4-level rubric per pair (self-hosted) | csn-python | 556 | gpu_ms=99088.7 | 0.0184 |
| Laya multilingual 322M yes/no per pair (self-hosted) | csn-python | 556 | gpu_ms=101081.95 | 0.0189 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | csn-python | 556 | gpu_ms=166761.17 | 0.0321 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | csn-python | 556 | gpu_ms=339625.34 | 0.0651 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | csn-python | 556 | gpu_ms=585985.79 | 0.1114 |
| Open-Jev 2B yes/no per pair (self-hosted) | csn-python | 16680 | input_tokens=8643484, output_tokens=0 | 0.2355 |
| Open-Jev 9B yes/no per pair (self-hosted) | csn-python | 16680 | input_tokens=8643484, output_tokens=0 | 1.1654 |
| Qwen3-Reranker-4B (self-hosted) | csn-python | 556 | gpu_ms=1817165.65 | 0.1363 |
| bge-reranker-v2-m3 (self-hosted) | csn-python | 556 | gpu_ms=846639.79 | 0.0635 |
| mxbai-rerank-base-v2 (self-hosted) | csn-python | 556 | gpu_ms=949729.77 | 0.0712 |
| Qwen3.5-4B yes/no per pair (self-hosted) | csn-python | 556 | gpu_ms=1601959.92 | 0.1201 |
| tev1-4B relevant / not per pair (self-hosted) | csn-python | 556 | gpu_ms=1847032.85 | 0.1385 |
| reflex 4B yes/no per pair (self-hosted) | csn-python | 16680 | input_tokens=11019735, output_tokens=0, state_tokens=8050695, question_tokens=2969040, state_cache_hit=0, images=0 | 0.2262 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | csn-python | 16680 | input_tokens=10476298, output_tokens=0 | 0.3725 |
| decider-2b v11 yes/no per pair (self-hosted) | csn-python | 16680 | input_tokens=8356549, output_tokens=0 | 0.0571 |
| Cohere Rerank 4 Pro | miracl-fr | 421 | search_units=421 | 1.0525 |
| Cohere Rerank 4 Fast | miracl-fr | 421 | search_units=421 | 0.8420 |
| ZeroEntropy zerank-2 | miracl-fr | 421 | total_tokens=1873503, total_bytes=8134231, inference_latency_s=135.22 | 0.0468 |
| DeepSeek V4.1 Flash P(yes) per pair | miracl-fr | 12630 | prompt_tokens=2316276, completion_tokens=12630, total_tokens=2328906, cost=0.34, is_byok=0 | 0.3410 |
| DeepSeek V4.1 Flash JSON, 30 in one call | miracl-fr | 421 | prompt_tokens=1569535, completion_tokens=88442, total_tokens=1657977, cost=0.26, is_byok=0 | 0.2643 |
| Jev yes/no per pair | miracl-fr | 12630 | input_tokens=6062386, output_tokens=277860 | 0.2546 |
| Jev 30 yes/no in one call | miracl-fr | 421 | input_tokens=2723737, output_tokens=229024 | 0.1144 |
| Jev one Choice + none | miracl-fr | 421 | input_tokens=1911207, output_tokens=131609 | 0.0803 |
| Jev 4-level rubric, 30 in one call | miracl-fr | 421 | input_tokens=3077377, output_tokens=191134 | 0.1292 |
| Jev 45 duels in one call (top 10) | miracl-fr | 421 | input_tokens=1551620, output_tokens=740118 | 0.0652 |
| Jev tournament (6 groups, then final) | miracl-fr | 842 | input_tokens=2613814, output_tokens=213554 | 0.1098 |
| Jev cascade (batch prune, then 8 pairs) | miracl-fr | 3789 | input_tokens=4384198, output_tokens=303120 | 0.1841 |
| Jev one Choice, passages reversed | miracl-fr | 269 | input_tokens=1221067, output_tokens=84109 | 0.0513 |
| Laya 421M yes/no per pair (self-hosted) | miracl-fr | 421 | gpu_ms=61238.86 | 0.0114 |
| Laya 421M 4-level rubric per pair (self-hosted) | miracl-fr | 421 | gpu_ms=63864.02 | 0.0119 |
| Laya multilingual 322M yes/no per pair (self-hosted) | miracl-fr | 421 | gpu_ms=25890.66 | 0.0048 |
| GLiNER2.5 small 74M, relevant / not per pair (self-hosted) | miracl-fr | 421 | gpu_ms=49544.36 | 0.0095 |
| GLiNER2.5 base 194M, relevant / not per pair (self-hosted) | miracl-fr | 421 | gpu_ms=98925.92 | 0.0188 |
| GLiNER2.5 multi 0.3B, relevant / not per pair (self-hosted) | miracl-fr | 421 | gpu_ms=119339.55 | 0.0227 |
| Open-Jev 2B yes/no per pair (self-hosted) | miracl-fr | 12630 | input_tokens=2821090, output_tokens=0 | 0.1325 |
| Open-Jev 9B yes/no per pair (self-hosted) | miracl-fr | 12630 | input_tokens=2821090, output_tokens=0 | 0.8064 |
| Qwen3-Reranker-4B (self-hosted) | miracl-fr | 421 | gpu_ms=694911.35 | 0.0521 |
| bge-reranker-v2-m3 (self-hosted) | miracl-fr | 421 | gpu_ms=227098.02 | 0.0170 |
| mxbai-rerank-base-v2 (self-hosted) | miracl-fr | 421 | gpu_ms=383223.6 | 0.0287 |
| Qwen3.5-4B yes/no per pair (self-hosted) | miracl-fr | 421 | gpu_ms=780916.84 | 0.0586 |
| tev1-4B relevant / not per pair (self-hosted) | miracl-fr | 421 | gpu_ms=820447.72 | 0.0615 |
| reflex 4B yes/no per pair (self-hosted) | miracl-fr | 12630 | input_tokens=4613344, output_tokens=0, state_tokens=2365204, question_tokens=2248140, state_cache_hit=4, images=0 | 0.1530 |
| Winnow-12B Q8 yes/no per pair (self-hosted) | miracl-fr | 12630 | input_tokens=3371275, output_tokens=0 | 0.1392 |
| decider-2b v11 yes/no per pair (self-hosted) | miracl-fr | 12630 | input_tokens=2604725, output_tokens=0 | 0.0198 |