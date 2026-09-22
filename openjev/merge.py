"""Merge the per-pod cache shards of an Open-Jev run and verify coverage before any pod is deleted.

    uv run openjev/merge.py <staging dir> [--write]

<staging dir>/<pod>/open-jev-*/<dataset>.<variant>.jsonl are the files pulled from every pod. One row per question
survives (an ok row is never overwritten by a failed one); every dataset and variant is checked against the candidate
lists, and --write stores the merged rows as cache/<model>/<dataset>.<variant>.jsonl.gz.
"""
import gzip, json, sys
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from common import DATASETS, EXTRA, CANDIDATES, read_jsonl  # noqa: E402

S = Path(sys.argv[1])
merged = defaultdict(dict)                       # (model, ds, variant) -> qid -> row
for p in sorted(S.glob("*/open-jev-*/*.jsonl")):
    model = p.parent.name; ds, variant, _ = p.name.split(".")
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line); cur = merged[(model, ds, variant)].get(r["qid"])
            if cur is None or r["ok"] or not cur["ok"]:
                merged[(model, ds, variant)][r["qid"]] = r
bad = 0
for model in sorted({k[0] for k in merged}):
    print(f"== {model}")
    for ds in DATASETS + EXTRA:
        rows = read_jsonl(CANDIDATES / f"{ds}.jsonl")
        for variant in ("present", "absent"):
            want = {r["qid"] for r in rows if r[variant]}
            if not want:
                continue
            got = merged.get((model, ds, variant), {})
            ok = sum(1 for r in got.values() if r["ok"]); failed = len(got) - ok; missing = len(want - set(got))
            bad += failed + missing
            print(f"  {ds:28s} {variant:8s} want {len(want):5d}  ok {ok:5d}  failed {failed:3d}  missing {missing:4d}" + ("" if failed == 0 and missing == 0 else "   <-- INCOMPLETE"))
            if "--write" in sys.argv and got:
                out = ROOT / "cache" / model / f"{ds}.{variant}.jsonl.gz"; out.parent.mkdir(parents=True, exist_ok=True)
                with gzip.open(out, "wt", encoding="utf-8") as f:
                    for qid in [r["qid"] for r in rows if r["qid"] in got]:
                        f.write(json.dumps(got[qid], ensure_ascii=False) + "\n")
print("TOTAL failed+missing:", bad)
