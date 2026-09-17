"""Regression tests for public evidence selection, scoring and sanitization."""
import tempfile
import unittest
import hashlib
import json
import re
import zipfile
from pathlib import Path
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import export_evidence as ex


def audit_export(output):
    """Check the actual public snapshot without ever printing credential values."""
    from dotenv import dotenv_values
    output = output.resolve()
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert set(m["id"] for m in manifest["models"]) == set(ex.MODELS)
    secrets = [value.encode() for value in dotenv_values(ex.ROOT / ".env").values() if isinstance(value, str) and len(value) >= 12]
    prefixes = re.compile(rb"(?<![A-Za-z0-9])(?:sk-(?:or-v1-)?[A-Za-z0-9_-]{20,}|hf_[A-Za-z0-9]{20,}|rpa_[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")
    scanned_files = scanned_entries = queries = 0
    def check_bytes(data, label):
        assert not any(secret in data for secret in secrets), f"Credential match in {label}; value suppressed"
        assert not prefixes.search(data), f"Credential-like content in {label}; value suppressed"
        assert b"C:\\\\Users\\\\hp" not in data and b"D:\\\\ACTIVE-PROJECTS" not in data, f"Private local path in {label}"
    for path in sorted(output.rglob("*.json")):
        data = path.read_bytes()
        check_bytes(data, path.relative_to(output).as_posix())
        json.loads(data)
        scanned_files += 1
    for dataset in manifest["datasets"]:
        index = json.loads((output / dataset["index_url"].removeprefix("data/")).read_text(encoding="utf-8"))
        assert len(index["queries"]) == dataset["queries_total"]
        assert index["dataset"]["models"] == dataset["models"]
        for query in index["queries"]:
            detail = json.loads((output / query["detail_url"].removeprefix("data/")).read_text(encoding="utf-8"))
            assert detail["qid"] == query["qid"]
            queries += 1
            for variant in detail["variants"].values():
                if variant["status"] != "available":
                    continue
                assert set(variant["models"]) == set(ex.MODELS)
                assert all(len(c["text"]) <= ex.MAX_CHARS for c in variant["candidates"])
                for model, result in variant["models"].items():
                    if result["status"] == "ok":
                        assert len(result["scores"]) == len(variant["candidates"])
                    if model.startswith(ex.QWEN_PREFIX) and result["status"] == "ok":
                        assert result["calls"][0]["usage"]["gpu_ms"] == result["query_ms"]
                        assert abs(result["cost_usd"] - result["query_ms"] / 3.6e6 * result["extra"]["usd_per_hour"]) < 1e-12
        for download in dataset["downloads"]:
            path = output / download["url"].removeprefix("data/")
            assert path.stat().st_size == download["bytes"] and path.stat().st_size < 25 * 1024 * 1024
            with zipfile.ZipFile(path) as archive:
                assert "LICENSES.json" in archive.namelist()
                for name in archive.namelist():
                    assert not Path(name).is_absolute() and ".." not in Path(name).parts
                    data = archive.read(name)
                    check_bytes(data, f"{path.name}/{name}")
                    json.loads(data)
                    scanned_entries += 1
                    if name.startswith("queries/"):
                        assert hashlib.sha256(data).digest() == hashlib.sha256((output / dataset["id"] / name).read_bytes()).digest()
    french = next(d for d in manifest["datasets"] if d["id"] == "miracl-fr")
    for model in ex.MODELS:
        if model.startswith(ex.QWEN_PREFIX):
            assert french["models"][model]["present_recorded"] == 0
    reversed_ = next(m for m in manifest["models"] if m["id"] == "qwen-rlcd-batch-reversed")
    assert set(reversed_["available_datasets"]) == set(ex.ENGLISH)
    assert reversed_["experiment_role"] == "order_sensitivity_diagnostic"
    print(json.dumps({"version": manifest["version"], "datasets": len(manifest["datasets"]), "models": len(manifest["models"]), "queries": queries, "json_files_scanned": scanned_files, "zip_entries_scanned": scanned_entries, "credential_matches": 0, "schema_scope_cost_and_archive_checks": "PASS"}))


class EvidenceTests(unittest.TestCase):
    def test_qwen_prompt_capture_never_loads_torch_or_changes_passage_mapping(self):
        with patch.dict(sys.modules, {"torch": None}):
            batch = ex.make_rlcd_prompt("qwen-rlcd-batch")
            pair = ex.make_rlcd_prompt("qwen-rlcd-pair")
            rubric = ex.make_rlcd_prompt("qwen-rlcd-rubric")
            reversed_ = ex.make_rlcd_prompt("qwen-rlcd-batch-reversed")
        self.assertEqual(len(batch["requests"][0]["schema"]), 30)
        self.assertEqual(batch["requests"][0]["temperature"], 1.0)
        self.assertEqual(pair["requests_per_query"], 30)
        self.assertEqual(len(pair["requests"][0]["schema"]), 1)
        self.assertEqual(rubric["requests"][0]["schema"]["p01"]["choices"], ["off-topic", "related", "partly", "fully"])
        self.assertIn("p01: <PASSAGE_30>", reversed_["requests"][0]["context"])
        self.assertIn("p30: <PASSAGE_01>", reversed_["requests"][0]["context"])

    def test_qwen_telemetry_is_preserved_without_pod_metadata(self):
        call = {"status": 200, "latency_ms": 1000, "cost_usd": .74 / 3600, "usage": {"gpu_ms": 1000, "token": "PRIVATE"},
                "raw": {"mode": "parallel_constrained_chunked", "pod_id": "PRIVATE", "headers": "PRIVATE",
                        "field_telemetry": {"p01": {"top_choices": [{"choice": "true", "probability": .75, "request_id": "PRIVATE"}], "private_path": "PRIVATE"}},
                        "per_passage": [{"prefill_ms": 2, "top_choices": [{"choice": "false", "probability": .25}]}]}}
        out = ex.sanitized_call(call)
        self.assertNotIn(b"PRIVATE", ex.encoded(out))
        self.assertEqual(out["usage"]["gpu_ms"], 1000)
        self.assertEqual(out["output"]["mode"], "parallel_constrained_chunked")
        self.assertEqual(out["output"]["field_telemetry"]["p01"]["top_choices"][0]["probability"], .75)

    def test_qwen_metadata_does_not_treat_gpu_estimate_as_api_cost(self):
        model = ex.model_metadata("qwen-rlcd-batch-reversed")
        self.assertEqual(model["family"], "Qwen RLCD")
        self.assertEqual(model["cost_basis"], "gpu_time_estimate")
        self.assertEqual(model["latency_basis"], "gpu_host_wall_clock")
        self.assertEqual(model["experiment_role"], "order_sensitivity_diagnostic")

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
    if sys.argv[1:2] == ["--audit-output"]:
        audit_export(Path(sys.argv[2]))
    else:
        unittest.main()
