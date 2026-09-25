"""Tests for bench.py: its scoring reproduces every row of the README's main table from cache/, and packing never lets
a failed response replace a good one. No network, no GPU; the table check reads every model's responses (~2 minutes).

    uv run python scripts/test_bench.py
"""
import gzip
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bench  # noqa: E402
from common import ROOT, read_jsonl  # noqa: E402

KEYS = {"Jev 4-level rubric, 30 in one call": "jev-score-batch", "Cohere Rerank 4 Pro": "cohere-pro",
        "Jev 30 yes/no in one call": "jev-noul-batch", "Jev one Choice + none": "jev-choice",
        "Cohere Rerank 4 Fast": "cohere-fast", "ZeroEntropy zerank-2": "zerank-2",
        "DeepSeek V4.1 Flash JSON, 30 in one call": "deepseek-json", "Jev cascade (batch prune, then 8 pairs)": "jev-cascade",
        "Jev yes/no per pair": "jev-noul-pair", "Jev tournament (6 groups, then final)": "jev-tournament",
        "DeepSeek V4.1 Flash P(yes) per pair": "deepseek-pair", "Jev 45 duels in one call (top 10)": "jev-duel",
        "Open-Jev 9B yes/no per pair": "open-jev-9b-noul-pair",
        "decider-2b v11 yes/no per pair": "decider-2b-noul-pair",
        "mxbai-rerank-base-v2": "mxbai-rerank-base-v2",
        "Qwen3-Reranker-4B": "qwen3-reranker-4b",
        "tev1-4B relevant / not per pair": "tev1-4b-pair",
        "bge-reranker-v2-m3": "bge-reranker-v2-m3",
        "reflex 4B yes/no per pair": "reflex-4b-noul-pair",
        "Qwen3.5-4B yes/no per pair": "qwen35-4b-yesno-pair",
        "Winnow-12B Q8 yes/no per pair": "winnow-12b-noul-pair", "Open-Jev 2B yes/no per pair": "open-jev-2b-noul-pair",
        "Laya 421M 4-level rubric per pair": "laya-score-pair", "Qwen2.5-1.5B RLCD, one passage per prompt": "qwen-rlcd-pair",
        "Laya 421M yes/no per pair": "laya-noul-pair", "GLiNER2.5 base 194M, relevant / not per pair": "gliner25-base-pair",
        "GLiNER2.5 multi 0.3B, relevant / not per pair": "gliner25-multi-pair",
        "GLiNER2.5 small 74M, relevant / not per pair": "gliner25-small-pair",
        "Laya multilingual 322M yes/no per pair": "laya-multi-noul-pair", "Qwen2.5-1.5B RLCD, 30 rubric keys": "qwen-rlcd-rubric",
        "Qwen2.5-1.5B RLCD, 30 yes/no keys": "qwen-rlcd-batch", "BM25 (floor)": "bm25"}


def readme_rows() -> list[str]:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    block = re.search(r"\| Model \| Runs on \|.*?\n\|[-|]+\|\n((?:\|.*\n)+)", text).group(1)
    return [line.rstrip("\r") for line in block.splitlines()]


class MainTable(unittest.TestCase):
    def test_bench_reproduces_every_readme_row(self):
        rows = readme_rows()
        self.assertEqual(len(rows), len(KEYS))
        for line in rows:
            cells = [c.strip() for c in line.strip("|").split("|")]
            with self.subTest(model=cells[0]):
                got = bench.fmt_row(cells[0], cells[1], bench.score(KEYS[cells[0]]))
                if cells[0] == "BM25 (floor)":      # the table writes BM25's time and cost as "–" and "0"
                    got = re.sub(r"\| 0 ms \| 0\.00 \|", "| – | 0 |", got)
                self.assertEqual(got, line)


class Pack(unittest.TestCase):
    def test_a_failed_retry_never_replaces_an_ok_answer(self):
        want = bench.wanted("scifact", "present")[:4]
        row = lambda q, ok: {"qid": q, "ok": ok, "scores": [0.5], "note": f"{q}-{ok}"}
        with tempfile.TemporaryDirectory() as d, patch.object(bench, "CACHE", Path(d)):
            folder = Path(d) / "m"
            folder.mkdir()
            with gzip.open(folder / "scifact.present.jsonl.gz", "wt", encoding="utf-8") as f:
                f.write(json.dumps(row(want[0], True)) + "\n" + json.dumps(row(want[1], False)) + "\n")
            (folder / "scifact.present.jsonl").write_text(
                json.dumps(row(want[0], False)) + "\n" + json.dumps(row(want[1], True)) + "\n" + json.dumps(row(want[2], False)) + "\n",
                encoding="utf-8")
            counts = bench.pack("m", "scifact", "present")
            self.assertFalse((folder / "scifact.present.jsonl").exists())
            packed = read_jsonl(folder / "scifact.present.jsonl")
        n = len(bench.wanted("scifact", "present"))
        self.assertEqual(counts, (n, 2, 1, n - 3))
        self.assertEqual([r["note"] for r in packed], [f"{want[0]}-True", f"{want[1]}-True", f"{want[2]}-False"])


class EndToEnd(unittest.TestCase):
    def test_smoke_then_full_run_then_the_row(self):
        """The one command's path on SciFact and NevIR against a stand-in for the server (a function answering every
        yes/no question), into a throwaway cache: smoke answers only the first questions, the full run answers the
        rest, packing leaves one gzipped file per list, and the row comes out complete."""
        import zlib
        import common
        import eval as ev
        import run as runner
        from rerankers import systemone as so

        def server(url, headers, body, **_):
            p = body["state"]["passage"]
            answers = {n: {"type": "noul", "noul": zlib.crc32(p.encode()) % 100 / 100} for n in body["questions"]}
            return 200, {"answers": answers, "usage": {"input_tokens": 100, "output_tokens": 0}}, 3.0, {}

        entry = load_entry({"base_url": "http://127.0.0.1:9/v1", "model": "m", "modes": ["noul-batch"], "max_context": 4096,
                            "passages_per_request": 30, "concurrency": 4, "price": {"gpu_usd_per_hour": 0.74},
                            "label": "Test model (a stand-in)", "runs_on": "Self-hosted: RTX 4090"})
        self.assertEqual(entry.keys, ["t-model-noul-pair"])      # a 4,096-token window cannot take 30 passages
        from rerankers import REGISTRY
        with tempfile.TemporaryDirectory() as d, patch.object(common, "CACHE", Path(d)), patch.object(ev, "CACHE", Path(d)), \
                patch.object(bench, "CACHE", Path(d)), patch.object(runner, "RESULTS", Path(d)), \
                patch.object(bench, "ENGLISH", ("scifact",)), patch.object(so, "post_json", server), \
                patch.dict(REGISTRY, {"t-model-noul-pair": lambda: so.make(entry.endpoint, "noul-pair", "t-model-noul-pair")}):
            bench.smoke(entry, 5, 4, False)
            first = bench.wanted("scifact", "present")[:5]
            self.assertEqual(sorted(bench.load_run("t-model-noul-pair", "scifact", "present")), sorted(first))
            bench.full(entry, 4, False)
            folder = Path(d) / "t-model-noul-pair"
            self.assertEqual(sorted(p.name for p in folder.iterdir()),
                             ["nevir.present.jsonl.gz", "scifact.absent.jsonl.gz", "scifact.present.jsonl.gz"])
            for ds, variant in (("scifact", "present"), ("scifact", "absent"), ("nevir", "present")):
                w, ok, failed, missing = bench.pack("t-model-noul-pair", ds, variant)
                self.assertEqual((ok, failed, missing), (w, 0, 0))
            m = bench.score("t-model-noul-pair")
            self.assertEqual((m["missing"], m["questions"]), ([], 264))
            self.assertIsNotNone(m["nevir"])
            row = bench.fmt_row("Test model yes/no per pair", "Self-hosted: RTX 4090", m)
            self.assertEqual(len(row.strip("|").split("|")), 9)
            self.assertTrue(bench.print_rows(entry))
            self.assertTrue((Path(d) / "runs.jsonl").exists())


def load_entry(fields: dict):
    import yaml
    from rerankers import registry
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "models.yaml"
        p.write_text(yaml.safe_dump({"models": {"t-model": fields}}), encoding="utf-8")
        return registry.load(p)["t-model"]


if __name__ == "__main__":
    unittest.main(verbosity=2)
