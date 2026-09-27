"""Offline retrieval comparison; uses JSON fixtures, never the application database."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import statistics
import sys
from time import perf_counter
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.services.retrieval import rank_articles


def evaluate(articles, cases, method):
    rows = []
    for case in cases:
        timings = []
        for _ in range(5):
            start = perf_counter()
            selected = rank_articles(case["question"], articles, method)
            timings.append((perf_counter() - start) * 1000)
        ids = [article.id for article in selected]
        relevant = set(case["relevant_ids"])
        first = next((i + 1 for i, identifier in enumerate(ids) if identifier in relevant), None)
        rows.append({**case, "method": method, "retrieved_ids": ids,
            "hit_at_1": int(bool(ids) and ids[0] in relevant) if relevant else None,
            "hit_at_3": int(first is not None) if relevant else None,
            "reciprocal_rank": 1 / first if first else 0,
            "abstained": int(not ids), "median_ms": statistics.median(timings)})
    return rows


def summarize(rows):
    answerable = [row for row in rows if row["relevant_ids"]]
    negative = [row for row in rows if not row["relevant_ids"]]
    mean = lambda values: statistics.mean(values) if values else None
    return {"answerable_count": len(answerable), "negative_count": len(negative),
        "hit_at_1": mean([r["hit_at_1"] for r in answerable]),
        "hit_at_3": mean([r["hit_at_3"] for r in answerable]),
        "mrr_at_3": mean([r["reciprocal_rank"] for r in answerable]),
        "negative_abstention_rate": mean([r["abstained"] for r in negative]),
        "median_retrieval_ms": statistics.median([r["median_ms"] for r in rows])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation/results")
    args = parser.parse_args()
    corpus_path, cases_path = ROOT / "evaluation/knowledge.json", ROOT / "evaluation/questions.json"
    articles = [SimpleNamespace(**a) for a in json.loads(corpus_path.read_text(encoding="utf-8"))]
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    if len({a.id for a in articles}) != len(articles) or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate fixture IDs")
    valid = {a.id for a in articles}
    if any(not set(c["relevant_ids"]) <= valid for c in cases):
        raise ValueError("Unknown relevance label")
    all_rows = []
    summaries = {}
    for method in ("baseline", "bm25"):
        rows = evaluate(articles, cases, method)
        all_rows.extend(rows)
        summaries[method] = {split: summarize([r for r in rows if r["split"] == split]) for split in ("development", "evaluation")}
    args.output.mkdir(parents=True, exist_ok=True)
    result = {"run_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (corpus_path, cases_path)},
        "limitations": "Synthetic developer-authored scenarios and labels, not an independent real-user benchmark. Retrieval metrics do not measure generated answer correctness. Timing excludes database/API/network.",
        "summaries": summaries, "cases": all_rows}
    (args.output / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    with (args.output / "cases.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)
    review_path = args.output / "human_review.csv"
    if not review_path.exists():
        write_review_template(review_path, cases)
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


def write_review_template(path, cases):
    with path.open("x", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["case_id", "question", "expected_article_ids", "answer", "correctness_0_2", "groundedness_0_2", "actionability_0_2", "reviewer", "notes"])
        for case in cases:
            writer.writerow([case["id"], case["question"], case["relevant_ids"], "", "", "", "", "", ""])


if __name__ == "__main__":
    main()
