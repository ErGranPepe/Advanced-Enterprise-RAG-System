import unittest
import numpy as np
from benchmark import BM25, top, rrf

class RetrievalRegressionTests(unittest.TestCase):
    def setUp(self):
        self.docs = ["a", "b", "c", "d"]

    def test_zero_scores_do_not_enter_lexical_candidates(self):
        scores = np.array([1.2, 0.0, 0.0, 0.0])
        self.assertEqual(top(scores, self.docs, True), ["a"])

    def test_dense_candidates_may_include_zero(self):
        scores = np.array([0., -0.5, 0.25, -0.2])
        self.assertEqual(top(scores, self.docs, False), ["c","a","d","b"])

    def test_no_lexical_match_returns_empty(self):
        bm = BM25(["orange apple", "banana pear"])
        self.assertEqual(top(bm.score("satellite"), ["a","b"], True), [])

    def test_rrf_uses_only_submitted_candidates(self):
        merged = rrf([["a"]], [["d","e","f"]])[0]
        self.assertEqual(merged[:3], ["a","d","e"])
        self.assertNotIn("b", merged)

    def test_rrf_deterministic_tie(self):
        self.assertEqual(rrf([["a"]], [["b"]])[0], ["a", "b"])

if __name__ == "__main__":
    unittest.main()
