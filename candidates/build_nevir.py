"""NevIR (Weller et al., 2023): 1,383 test pairs of near-identical passages that differ by a negation, each with two
questions; question 1 is answered by passage 1, question 2 by passage 2. Every question becomes a candidate row with
exactly those two passages, in the same order (passage 1, passage 2) for both questions, so a model that ignores the
negation gets one of the two wrong. BM25 over the two passages is the floor. Scored by nevir_eval.py (paired accuracy),
never in the ranking averages. Output: candidates/nevir.jsonl and nevir.docs.jsonl, same shape as the other sets.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bm25s
import Stemmer
from huggingface_hub import hf_hub_download

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import CANDIDATES, DATA, truncate, write_jsonl  # noqa: E402

STEMMER = Stemmer.Stemmer("english")


def bm25_pair(query: str, docs: list[str]) -> list[float]:
    idx = bm25s.BM25()
    idx.index(bm25s.tokenize(docs, stopwords="en", stemmer=STEMMER, show_progress=False), show_progress=False)
    res, scores = idx.retrieve(bm25s.tokenize([query], stopwords="en", stemmer=STEMMER, show_progress=False), k=len(docs), show_progress=False)
    out = [0.0] * len(docs)
    for i, s in zip(res[0], scores[0]):
        out[int(i)] = float(s)
    return out


def main() -> None:
    path = hf_hub_download("orionweller/NevIR", "test.jsonl", repo_type="dataset", local_dir=DATA / "raw" / "NevIR")
    pairs = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    rows, docs = [], []
    for r in pairs:
        d1, d2 = f"{r['id']}-d1", f"{r['id']}-d2"
        texts = [truncate(r["doc1"]), truncate(r["doc2"])]
        docs += [{"did": d1, "text": texts[0]}, {"did": d2, "text": texts[1]}]
        for qn, (q, rel) in enumerate(((r["q1"], d1), (r["q2"], d2)), start=1):
            b = bm25_pair(q, texts)
            rows.append({"qid": f"{r['id']}-q{qn}", "pair": r["id"], "query": q, "relevant": {rel: 1},
                         "present": [{"did": d1, "bm25": b[0]}, {"did": d2, "bm25": b[1]}], "absent": None,
                         "n_rel_total": 1, "n_rel_top30": 1, "rel_ranks": [1 if rel == d1 else 2]})
    write_jsonl(CANDIDATES / "nevir.jsonl", rows)
    write_jsonl(CANDIDATES / "nevir.docs.jsonl", docs)
    print(f"nevir: {len(pairs)} pairs, {len(rows)} questions, {len(docs)} passages -> {CANDIDATES / 'nevir.jsonl'}")


if __name__ == "__main__":
    main()
