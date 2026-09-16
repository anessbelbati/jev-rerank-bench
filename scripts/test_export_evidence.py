"""Regression tests for public evidence selection, scoring and sanitization."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_evidence as ex


class EvidenceTests(unittest.TestCase):
    def test_stable_and_pessimistic_ties(self):
        row = {"dids": ["a", "b"], "scores": [.5, .5]}
        result = ex.metrics(row, {"a": 1}, True)
        self.assertEqual(ex.order(row), ["a", "b"])
        self.assertEqual(result["ndcg10"], 1)
        self.assertLess(result["ndcg10_ties_against"], 1)
        self.assertTrue(result["tied_top"])
        self.assertFalse(ex.metrics(row, {"a": 1}, True, True)["question_correct"])

    def test_missing_and_ineligible_are_not_zero_scores(self):
        self.assertEqual(ex.export_row(None, [{"did": "a"}], {"a": 1}, True)["status"], "missing")
        self.assertIsNone(ex.export_row(None, [{"did": "a"}], {"a": 1}, True)["scores"])
        self.assertIsNone(ex.metrics({"dids": ["a"], "scores": [2]}, {"b": 1}, False)["ndcg10"])

    def test_latest_plain_rows_override_gzip_and_earlier_rows(self):
        with patch.object(ex, "read_jsonl", return_value=[{"qid": "1", "scores": [1]}, {"qid": "2", "scores": [2]}, {"qid": "1", "scores": [3]}]):
            rows, superseded = ex.latest("model", "dataset", "present")
        self.assertEqual(rows["1"]["scores"], [3])
        self.assertEqual(superseded, 1)

    def test_alignment_is_checked(self):
        row = {"ok": True, "dids": ["b", "a"], "scores": [1, 2]}
        self.assertEqual(ex.row_status(row, [{"did": "a"}, {"did": "b"}]), "invalid_candidate_alignment")

    def test_provider_metadata_is_not_exported(self):
        call = {"status": 200, "latency_ms": 2, "cost_usd": .1, "error": None,
                "usage": {"input_tokens": 4, "request_id": "PRIVATE"},
                "raw": {"id": "PRIVATE", "headers": {"Authorization": "PRIVATE"}, "model": "m", "answers": {"a": {"noul": .5, "request_id": "PRIVATE"}}, "results": [{"index": 0, "relevance_score": .5, "document": "PRIVATE"}]}}
        output = ex.encoded(ex.sanitized_call(call))
        self.assertNotIn(b"PRIVATE", output)
        self.assertIn(b'"noul":0.5', output)

    def test_macro_query_weighting_and_cost_population(self):
        datasets = []
        for name, n, value, cost_n, cost in [("a", 1, .2, 4, 4), ("b", 3, .8, 6, 6)]:
            row = {k: value for k in ex.METRICS}
            row.update(n=n, cost_queries=cost_n, cost_usd_present=cost, coverage_complete=True, missing=0, failed=0)
            datasets.append({"id": name, "queries_total": cost_n, "queries_eligible": n, "models": {m: dict(row) for m in ex.MODELS}})
        result = ex.aggregate("original8", "test", datasets)["models"]["bm25"]
        self.assertAlmostEqual(result["macro"]["ndcg10"], .5)
        self.assertAlmostEqual(result["query_weighted"]["ndcg10"], .65)
        self.assertEqual(result["cost_queries"], 10)
        self.assertEqual(result["cost_per_1k_queries"], 1000)


if __name__ == "__main__":
    unittest.main()
