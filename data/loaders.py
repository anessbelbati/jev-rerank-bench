"""Download the public datasets and expose them in one shape.

English (BEIR, test split):
- scifact    : 300 scientific claims over 5,183 abstracts.
- fiqa       : 648 finance questions over 57,638 passages.
- nq         : Natural Questions, real Google searches over 2.68M Wikipedia passages; a fixed random sample of the
               3,452 test questions keeps the cost bounded (SAMPLE below).
- nfcorpus   : 323 medical and nutrition questions over 3,633 documents, graded relevance.
- trec-covid : 50 questions about COVID-19 over 171,332 papers, deep graded judgements.
French:
- miracl-fr  : MIRACL French dev as packaged by MTEB for reranking: 343 queries, each with its own 100-passage pool.

Relevance labels come with the datasets; a passage is relevant when its label is above 0.
"""
from __future__ import annotations

import ast
import csv
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download, list_repo_files

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import DATA  # noqa: E402

RAW = DATA / "raw"
SAMPLE = {"nq": (500, 0)}   # dataset -> (number of labelled queries kept, random seed)


@dataclass
class Dataset:
    name: str
    lang: str                          # "english" or "french": drives the BM25 stemmer and stopwords
    queries: dict[str, str]            # qid -> query text (only queries that have labels)
    corpus: dict[str, str]             # did -> passage text (title + body)
    qrels: dict[str, dict[str, int]]   # qid -> {did: grade > 0}
    pools: dict[str, list[str]] | None # qid -> candidate dids, when the dataset ships a per-query pool; else the corpus


def _get(repo: str, filename: str) -> Path:
    return Path(hf_hub_download(repo_id=repo, filename=filename, repo_type="dataset", local_dir=RAW / repo.split("/")[-1]))


def _parquet_rows(path: Path) -> list[dict]:
    return pq.read_table(path).to_pylist()


def _folder_rows(repo: str, folder: str) -> list[dict]:
    """All parquet shards under repo/folder, in name order."""
    rows = []
    for f in sorted(x for x in list_repo_files(repo, repo_type="dataset") if x.startswith(folder + "/") and x.endswith(".parquet")):
        rows.extend(_parquet_rows(_get(repo, f)))
    return rows


def _doc(row: dict) -> str:
    title = (row.get("title") or "").strip()
    text = (row.get("text") or "").strip()
    return f"{title}\n{text}".strip() if title else text


def _beir(name: str) -> Dataset:
    corpus = {str(r["_id"]): _doc(r) for r in _folder_rows(f"BeIR/{name}", "corpus")}
    queries_all = {str(r["_id"]): r["text"] for r in _folder_rows(f"BeIR/{name}", "queries")}
    qrels: dict[str, dict[str, int]] = {}
    with _get(f"BeIR/{name}-qrels", "test.tsv").open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            grade = int(float(row["score"]))
            if grade > 0:
                qrels.setdefault(str(row["query-id"]), {})[str(row["corpus-id"])] = grade
    qids = sorted(q for q in qrels if q in queries_all)
    if name in SAMPLE:
        n, seed = SAMPLE[name]
        qids = sorted(random.Random(seed).sample(qids, min(n, len(qids))))
    queries = {q: queries_all[q] for q in qids}
    qrels = {q: qrels[q] for q in qids}
    return Dataset(name, "english", queries, corpus, qrels, None)


def _miracl_fr() -> Dataset:
    repo = "mteb/MIRACLReranking"
    queries = {r["_id"]: r["text"] for r in _parquet_rows(_get(repo, "fr-queries/dev-00000-of-00001.parquet"))}
    corpus = {r["_id"]: _doc(r) for r in _parquet_rows(_get(repo, "fr-corpus/dev-00000-of-00001.parquet"))}
    qrels: dict[str, dict[str, int]] = {}
    for r in _parquet_rows(_get(repo, "fr-qrels/dev-00000-of-00001.parquet")):
        grade = int(r["score"])
        if grade > 0:
            qrels.setdefault(r["query-id"], {})[r["corpus-id"]] = grade
    pools: dict[str, list[str]] = {}
    for r in _parquet_rows(_get(repo, "fr-top_ranked/dev-00000-of-00001.parquet")):
        ids = r["corpus-ids"]
        if isinstance(ids, str):
            ids = ast.literal_eval(ids)
        pools[r["query-id"]] = list(ids)
    queries = {q: t for q, t in queries.items() if q in qrels and q in pools}
    return Dataset("miracl-fr", "french", queries, corpus, qrels, pools)


MTEB = {   # name -> (repo, subset prefix, split). Files live under <subset>-corpus/, <subset>-queries/, <subset>-qrels/.
    "bright-biology": ("mteb/BrightRetrieval", "biology", "standard"),      # reasoning-intensive StackExchange questions -> web docs
    "bright-economics": ("mteb/BrightRetrieval", "economics", "standard"),
    "bright-earth_science": ("mteb/BrightRetrieval", "earth_science", "standard"),
    "bright-psychology": ("mteb/BrightRetrieval", "psychology", "standard"),
    "bright-robotics": ("mteb/BrightRetrieval", "robotics", "standard"),
    "bright-stackoverflow": ("mteb/BrightRetrieval", "stackoverflow", "standard"),
    "bright-sustainable_living": ("mteb/BrightRetrieval", "sustainable_living", "standard"),
    "csn-python": ("mteb/CodeSearchNetRetrieval", "python", "test"),       # docstring -> the Python function it documents
}
SAMPLE["csn-python"] = (300, 0)


def _mteb(name: str) -> Dataset:
    repo, sub, split = MTEB[name]
    def rows(kind):
        return [r for r in _folder_rows(repo, f"{sub}-{kind}") ]
    corpus = {str(r.get("_id", r.get("id"))): _doc(r) for r in rows("corpus")}
    queries_all = {str(r.get("_id", r.get("id"))): r["text"] for r in rows("queries")}
    qrels: dict[str, dict[str, int]] = {}
    for r in rows("qrels"):
        grade = int(float(r["score"]))
        if grade > 0:
            qrels.setdefault(str(r["query-id"]), {})[str(r["corpus-id"])] = grade
    qids = sorted(q for q in qrels if q in queries_all)
    if name in SAMPLE:
        n, seed = SAMPLE[name]
        qids = sorted(random.Random(seed).sample(qids, min(n, len(qids))))
    return Dataset(name, "english", {q: queries_all[q] for q in qids}, corpus, {q: qrels[q] for q in qids}, None)


def load(name: str) -> Dataset:
    if name == "miracl-fr":
        return _miracl_fr()
    if name in MTEB:
        return _mteb(name)
    return _beir(name)


if __name__ == "__main__":
    for n in sys.argv[1:] or ("scifact", "fiqa", "nq", "nfcorpus", "trec-covid", "miracl-fr"):
        d = load(n)
        rel_per_q = [len(v) for v in d.qrels.values()]
        print(f"{d.name}: {len(d.queries)} labelled queries, {len(d.corpus)} passages, "
              f"{sum(rel_per_q)} relevant labels ({sum(rel_per_q)/len(rel_per_q):.2f} per query), "
              f"pool={'per-query ' + str(len(next(iter(d.pools.values())))) if d.pools else 'whole corpus'}")
