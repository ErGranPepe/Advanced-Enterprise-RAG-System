"""Regression tests for the per-query audit utility."""
import csv
import tempfile
import unittest
from pathlib import Path

from auditar_consultas import audit_csv


class AuditCsvTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "per_query.csv"
        self.base = "BM25"
        self.hybrid = "BM25 + MiniLM (RRF)"

    def tearDown(self):
        self.dir.cleanup()

    def write_rows(self, rows):
        with self.path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["method", "qid", "query", "nDCG@10", "top10", "relevantes"])
            writer.writerows(rows)

    def test_counts_and_largest_loss(self):
        self.write_rows([
            [self.base, "q1", "A", 1.0, "a", "a"],
            [self.hybrid, "q1", "A", 0.3155, "b;a", "a"],
            [self.base, "q2", "B", 0.4, "b", "b"],
            [self.hybrid, "q2", "B", 0.7, "b;a", "b"],
        ])
        report = audit_csv(self.path)
        self.assertEqual((report["queries"], report["wins"], report["losses"], report["ties"]), (2, 1, 1, 0))
        self.assertEqual(report["worst"][0]["qid"], "q1")

    def test_missing_pair_rejected(self):
        self.write_rows([[self.base, "q1", "A", 1, "a", "a"]])
        with self.assertRaises(ValueError):
            audit_csv(self.path)

    def test_threshold_filter(self):
        self.write_rows([
            [self.base, "q1", "A", 0.5, "a", "a"],
            [self.hybrid, "q1", "A", 0.45, "a", "a"],
            [self.base, "q2", "B", 0.9, "b", "b"],
            [self.hybrid, "q2", "B", 0.6, "b;a", "b"],
        ])
        report = audit_csv(self.path, threshold=0.1)
        self.assertEqual(report["losses"], 2)
        self.assertEqual(report["regressions_above_threshold"], 1)
        self.assertEqual(report["worst"][0]["qid"], "q2")


if __name__ == "__main__":
    unittest.main()
