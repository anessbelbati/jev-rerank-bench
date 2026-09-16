"""Build the fixed candidate lists every model reranks: BM25 top-30 per query, plus the "absent" twin.

BM25 = bm25s with a Snowball stemmer and stopwords for the dataset's language. For SciFact and FiQA the index is the
whole corpus; for MIRACL French it is each query's own 100-passage pool (the full French Wikipedia corpus is 14.6M
passages, far beyond a laptop, and the pool is the standard reranking set MTEB publishes).

The absent twin exists only for queries whose BM25 top-30 holds at least one relevant passage: every relevant passage
(by the dataset's labels) is dropped from the BM25 ranking and the list is refilled from further down, so the model
sees 30 passages that are all on-topic and none of which answers the query.
"""
from __future__ import annotations

import sys
from pathlib import Path

import bm25s
import Stemmer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import CANDIDATES, DATASETS, TOP_K, write_jsonl  # noqa: E402
from data.loaders import Dataset, load  # noqa: E402

DEPTH = 100   # BM25 ranks kept per query, so the absent twin can be refilled without a second retrieval


def _stopwords(lang: str):
    return "en" if lang == "english" else "fr"


def _rank(ds: Dataset, qid: str, texts: list[str], dids: list[str], stemmer, k: int):
    """Score one query against `texts` and return [(did, bm25)] best first."""
    tokens = bm25s.tokenize(texts, stopwords=_stopwords(ds.lang), stemmer=stemmer, show_progress=False)
    r = bm25s.BM25()
    r.index(tokens, show_progress=False)
    q = bm25s.tokenize([ds.queries[qid]], stopwords=_stopwords(ds.lang), stemmer=stemmer, show_progress=False)
    idx, sc = r.retrieve(q, k=min(k, len(texts)), show_progress=False)
    return [(dids[i], float(s)) for i, s in zip(idx[0], sc[0])]


def build(name: str) -> None:
    ds = load(name)
    stemmer = Stemmer.Stemmer(ds.lang)
    ranked: dict[str, list[tuple[str, float]]] = {}
    if ds.pools is None:
        dids = list(ds.corpus)
        texts = [ds.corpus[d] for d in dids]
        tokens = bm25s.tokenize(texts, stopwords=_stopwords(ds.lang), stemmer=stemmer)
        r = bm25s.BM25()
        r.index(tokens)
        qids = list(ds.queries)
        q = bm25s.tokenize([ds.queries[x] for x in qids], stopwords=_stopwords(ds.lang), stemmer=stemmer)
        idx, sc = r.retrieve(q, k=DEPTH)
        for row, i_row, s_row in zip(qids, idx, sc):
            ranked[row] = [(dids[i], float(s)) for i, s in zip(i_row, s_row)]
    else:
        for qid in ds.queries:
            pool = ds.pools[qid]
            ranked[qid] = _rank(ds, qid, [ds.corpus[d] for d in pool], pool, stemmer, DEPTH)

    rows, used = [], set()
    for qid, lst in ranked.items():
        rel = ds.qrels[qid]
        present = lst[:TOP_K]
        n_rel_top = sum(1 for d, _ in present if d in rel)
        absent = [(d, s) for d, s in lst if d not in rel][:TOP_K] if n_rel_top else None
        if absent is not None and len(absent) < TOP_K:
            absent = None   # not enough non-relevant passages in BM25's top 100 to build a full-size twin
        rows.append({
            "qid": qid, "query": ds.queries[qid], "relevant": rel,
            "present": [{"did": d, "bm25": s} for d, s in present],
            "absent": [{"did": d, "bm25": s} for d, s in absent] if absent else None,
            "n_rel_total": len(rel), "n_rel_top30": n_rel_top,
            "rel_ranks": [i + 1 for i, (d, _) in enumerate(lst) if d in rel],
        })
        used.update(d for d, _ in present)
        if absent:
            used.update(d for d, _ in absent)
    write_jsonl(CANDIDATES / f"{name}.jsonl", rows)
    write_jsonl(CANDIDATES / f"{name}.docs.jsonl", ({"did": d, "text": ds.corpus[d]} for d in sorted(used)))
    n = len(rows)
    hit = sum(1 for r in rows if r["n_rel_top30"])
    top1 = sum(1 for r in rows if r["present"] and r["present"][0]["did"] in r["relevant"])
    print(f"{name}: {n} queries; BM25 top-30 holds a relevant passage for {hit} ({hit/n:.1%}); "
          f"BM25 top-1 relevant for {top1} ({top1/n:.1%}); absent twins: {sum(1 for r in rows if r['absent'])}; "
          f"{len(used)} distinct passages written")


if __name__ == "__main__":
    for n in sys.argv[1:] or DATASETS:
        build(n)
