"""Audit per-query regressions between two retrieval methods.

Usage:
  python auditar_consultas.py resultados/scifact/per_query.csv
  python auditar_consultas.py resultados/nfcorpus/per_query.csv --top 20 --threshold 0.10

No dependencies outside Python's standard library.
"""
import argparse
import csv
import json
from pathlib import Path


def audit_csv(path, baseline="BM25", candidate="BM25 + MiniLM (RRF)", top=10, threshold=0.0):
    grouped = {}
    with Path(path).open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            method = row["method"]
            if method not in (baseline, candidate):
                continue
            grouped.setdefault(row["qid"], {})[method] = row

    if not grouped:
        raise ValueError("No relevant queries found")
    if any(baseline not in runs or candidate not in runs for runs in grouped.values()):
        raise ValueError("Missing a method for one or more queries: cannot compare paired results")

    records = []
    for qid, pair in grouped.items():
        base = pair[baseline]
        current = pair[candidate]
        difference = float(current["nDCG@10"]) - float(base["nDCG@10"])
        records.append({
            "qid": qid,
            "query": base["query"],
            "bm25_ndcg_at_10": round(float(base["nDCG@10"]), 6),
            "hybrid_ndcg_at_10": round(float(current["nDCG@10"]), 6),
            "delta": round(difference, 6),
            "bm25_top10": base["top10"],
            "hybrid_top10": current["top10"],
            "relevant_ids": base["relevantes"],
        })

    eps = 1e-9
    result = {
        "queries": len(records),
        "wins": sum(r["delta"] > eps for r in records),
        "losses": sum(r["delta"] < -eps for r in records),
        "ties": sum(abs(r["delta"]) <= eps for r in records),
        "mean_delta": round(sum(r["delta"] for r in records) / len(records), 6),
        "threshold": threshold,
        "regressions_above_threshold": sum(r["delta"] < -threshold - eps for r in records),
        "worst": sorted((r for r in records if r["delta"] < -threshold - eps),
                        key=lambda r: (r["delta"], r["qid"]))[:top],
        "best": sorted((r for r in records if r["delta"] > threshold + eps),
                       key=lambda r: (-r["delta"], r["qid"]))[:top],
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file", help="per_query.csv produced by benchmark.py")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--threshold", type=float, default=0.0,
                        help="Only show changes larger than this absolute nDCG@10 delta")
    parser.add_argument("--out", help="Optional path to save the JSON report")
    args = parser.parse_args()
    if args.top < 0 or args.threshold < 0:
        parser.error("top and threshold must be nonnegative")
    result = audit_csv(args.csv_file, top=args.top, threshold=args.threshold)
    payload = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
