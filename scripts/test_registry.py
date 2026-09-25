"""Tests for models.yaml (rerankers/registry.py): the one-passage fallback, the checks on each entry, and the entries
the repo ships, replayed against their saved responses. No network, no GPU.

    uv run python scripts/test_registry.py
"""
import ast
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import rerankers.jev as jev  # noqa: E402
from common import CACHE, CANDIDATES, ROOT, read_jsonl, truncate  # noqa: E402
from rerankers import KEY_ENTRY, MODELS, REGISTRY  # noqa: E402
from rerankers import registry as R  # noqa: E402
from rerankers import systemone as so  # noqa: E402

NEED = R.sizes()
GOOD = {"base_url": "http://127.0.0.1:9/v1", "model": "m", "modes": ["noul-pair"], "max_context": 32768,
        "passages_per_request": 30, "concurrency": 2}


def run_modes(modes, max_context, passages):
    return {s.asked: s.mode for s in R.plan("x", modes, max_context, passages, NEED)}


def load_yaml(entries: dict):
    import yaml
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "models.yaml"
        p.write_text(yaml.safe_dump({"models": entries}), encoding="utf-8")
        return R.load(p)


class Fallback(unittest.TestCase):
    def test_a_server_that_takes_30_runs_every_mode_as_asked(self):
        self.assertEqual(run_modes(list(so.MODES), 32768, 30), {m: m for m in so.MODES})

    def test_a_small_window_runs_the_one_passage_forms(self):
        self.assertEqual(run_modes(["noul-batch", "score-batch", "choice", "duel", "noul-pair"], 16384, 30),
                         {"noul-batch": "noul-pair", "score-batch": "score-pair", "choice": "noul-pair",
                          "duel": "noul-pair", "noul-pair": "noul-pair"})

    def test_a_one_passage_server_falls_back_whatever_its_window(self):
        got = run_modes(["tournament", "cascade", "choice-reversed", "score-batch"], 1_000_000, 1)
        self.assertEqual(got, {"tournament": "noul-pair", "cascade": "noul-pair", "choice-reversed": "noul-pair",
                               "score-batch": "score-pair"})

    def test_duel_needs_ten_passages_not_thirty(self):
        self.assertEqual(run_modes(["duel", "noul-batch"], 32768, 10), {"duel": "duel", "noul-batch": "noul-pair"})

    def test_modes_that_fall_back_to_the_same_form_run_once(self):
        e = load_yaml({"small": {**GOOD, "modes": ["noul-batch", "choice", "noul-pair"], "max_context": 8192}})["small"]
        self.assertEqual(e.keys, ["small-noul-pair"])

    def test_a_window_too_small_for_one_passage_is_flagged(self):
        (step,) = R.plan("x", ["noul-pair"], 4096, 30, NEED)
        self.assertIn("WARNING", step.note)
        (step,) = R.plan("x", ["noul-pair"], 16384, 30, NEED)
        self.assertNotIn("WARNING", step.note)


class EntryChecks(unittest.TestCase):
    def bad(self, name, e):
        with self.assertRaises(SystemExit):
            load_yaml({name: e})

    def test_a_good_entry_loads(self):
        e = load_yaml({"ok-model": {**GOOD, "key_env": "SOME_KEY", "price": {"input_per_m": 0.05}}})["ok-model"]
        self.assertEqual((e.endpoint.url, e.endpoint.key_env, e.endpoint.input_per_m, e.concurrency),
                         ("http://127.0.0.1:9/v1/systemone", "SOME_KEY", 0.05, 2))

    def test_each_required_field(self):
        for f in R.REQUIRED:
            self.bad("m", {k: v for k, v in GOOD.items() if k != f})

    def test_typos_and_bad_values(self):
        self.bad("m", {**GOOD, "max_contxt": 4096})
        self.bad("m", {**GOOD, "modes": ["noul-pairs"]})
        self.bad("m", {**GOOD, "modes": []})
        self.bad("m", {**GOOD, "concurrency": 0})
        self.bad("m", {**GOOD, "max_context": "32k"})
        self.bad("m", {**GOOD, "price": {"usd": 1}})
        self.bad("Bad Name", GOOD)

    def test_a_key_pasted_where_its_name_belongs_is_refused(self):
        self.bad("m", {**GOOD, "key_env": "sk-or-v1-not-a-real-key"})


class Replies(unittest.TestCase):
    """A reply the adapter cannot read makes that question fail with a reason; it never stops the run."""
    NOUL = {"relevant": {"type": "noul", "instructions": "q", "criteria": {"true": "t", "false": "f"}}}
    SCORE = {"relevant": {"type": "score", "instructions": "q", "criteria": so.RUBRIC}}

    def ask(self, questions, reply):
        real = so.post_json
        so.post_json = lambda *a, **k: (200, reply, 5.0, {})
        try:
            return so._ask(so.Endpoint("http://127.0.0.1:9/v1", "m"), {"query": "q", "passage": "p"}, questions)
        finally:
            so.post_json = real

    def test_readable_replies_pass(self):
        self.assertIsNotNone(self.ask(self.NOUL, {"answers": {"relevant": {"noul": 0.4}}})[1])
        legend = {str(i): c for i, c in enumerate(so.RUBRIC)}
        self.assertIsNotNone(self.ask(self.SCORE, {"answers": {"relevant": {"legend": legend, "probabilities": {"0": 0.1, "1": 0.2, "2": 0.3, "3": 0.4}}}})[1])
        self.assertIsNotNone(self.ask(self.SCORE, {"answers": {"relevant": {"score": 0.7}}})[1])

    def test_unreadable_replies_fail_with_a_reason(self):
        cases = [(self.NOUL, {"result": 1}), (self.NOUL, {"answers": {}}), (self.NOUL, {"answers": {"relevant": {"noul": "high"}}}),
                 (self.SCORE, {"answers": {"relevant": {"legend": {"0": "bad", "1": "worse"}, "probabilities": {"0": 1.0, "1": 0.0}}}}),
                 (self.SCORE, {"answers": {"relevant": {"confidence": 0.9}}})]
        for questions, reply in cases:
            with self.subTest(reply=reply):
                call, body = self.ask(questions, reply)
                self.assertIsNone(body)
                self.assertTrue(call.error)

    def test_every_saved_jev_reply_is_readable(self):
        row = read_jsonl(CACHE / "jev-score-batch" / "scifact.present.jsonl")[0]
        questions = {f"p{i + 1:02d}": {"type": "score", "criteria": so.RUBRIC} for i in range(len(row["dids"]))}
        self.assertIsNone(so._unreadable(questions, row["calls"][0]["raw"]))


class ShippedEntries(unittest.TestCase):
    def test_shipped_entries_and_the_open_jev_cache_folders(self):
        self.assertEqual({n: e.keys for n, e in MODELS.items()},
                         {"open-jev-2b": ["open-jev-2b-noul-pair"], "open-jev-9b": ["open-jev-9b-noul-pair"],
                          "reflex-4b": ["reflex-4b-noul-pair"], "winnow-12b": ["winnow-12b-noul-pair"],
                          "decider-2b": ["decider-2b-noul-pair"]})
        for key in ("open-jev-2b-noul-pair", "open-jev-9b-noul-pair"):
            self.assertTrue((CACHE / key).is_dir())
            self.assertEqual(KEY_ENTRY[key].concurrency, 2)

    def test_built_in_models_are_untouched(self):
        self.assertIsInstance(REGISTRY["jev-noul-pair"](), jev.JevNoulPair)
        self.assertIsInstance(REGISTRY["open-jev-9b-noul-pair"](), so.NoulPair)

    def test_open_jev_entries_rebuild_the_sept_22_requests_and_scores(self):
        """Saved Open-Jev responses (SciFact, both variants, both sizes) replayed through the models.yaml entry: the
        same request bodies jev.py sent the Open-Jev servers (JEV_MODEL=open-jev) and the saved scores exactly."""
        cands = {r["qid"]: r for r in read_jsonl(CANDIDATES / "scifact.jsonl")}
        docs = {r["did"]: r["text"] for r in read_jsonl(CANDIDATES / "scifact.docs.jsonl")}
        real = so.post_json
        saved_model = jev.MODEL
        rows = 0
        try:
            jev.MODEL = "open-jev"
            for key in ("open-jev-2b-noul-pair", "open-jev-9b-noul-pair"):
                for variant in ("present", "absent"):
                    for row in read_jsonl(CACHE / key / f"scifact.{variant}.jsonl"):
                        if not row["ok"]:
                            continue
                        texts = [truncate(docs[c["did"]]) for c in cands[row["qid"]][variant]]
                        sent = {}
                        for side, mod, build in (("old", jev, jev.JevNoulPair), ("new", so, REGISTRY[key])):
                            calls, bodies = iter(row["calls"]), []

                            def fake(url, headers, body, **_):
                                c = next(calls)
                                bodies.append(json.dumps(body))
                                return c["status"], c["raw"], c["latency_ms"], {}
                            mod.post_json = fake
                            res = build().rerank(cands[row["qid"]]["query"], texts)
                            sent[side] = bodies
                        self.assertEqual(sent["old"], sent["new"])
                        self.assertEqual(res.scores, row["scores"])
                        rows += 1
        finally:
            so.post_json = jev.post_json = real
            jev.MODEL = saved_model
        self.assertGreater(rows, 1000)

    def test_score_pair_asks_what_laya_score_pair_was_asked(self):
        tree = ast.parse((ROOT / "small_models_runner.py").read_text(encoding="utf-8"))
        consts = {t.id: ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                  for t in n.targets if isinstance(t, ast.Name) and t.id in ("SCORE_QUESTION", "RUBRIC")}
        self.assertEqual((so.SCORE_QUESTION, so.RUBRIC), (consts["SCORE_QUESTION"], consts["RUBRIC"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
