
import tempfile
import unittest
from pathlib import Path


from ai_nurse_scr import metrics


class TestMetrics(unittest.TestCase):
    def test_classification_metrics(self):
        true = [True, False, True, True, False]
        pred = [True, False, False, True, False]
        m = metrics.classification_metrics(true, pred)
        self.assertAlmostEqual(m["precision"], 1.0)
        self.assertAlmostEqual(m["recall"], 2 / 3)
        self.assertAlmostEqual(m["f1"], 0.8)
        self.assertAlmostEqual(m["accuracy"], 4 / 5)

    def test_zero_division(self):
        m = metrics.classification_metrics([], [])
        self.assertEqual(m["precision"], 0.0)
        self.assertEqual(m["recall"], 0.0)
        self.assertEqual(m["f1"], 0.0)
        self.assertEqual(m["accuracy"], 0.0)

    def test_chunk_statistics(self):
        chunks = [["a", "b", "c"], ["d"], ["e", "f"]]
        stats = metrics.chunk_statistics(chunks)
        self.assertEqual(stats["num_chunks"], 3)
        self.assertAlmostEqual(stats["avg_tokens"], 2.0)
        self.assertEqual(stats["max_tokens"], 3)

    def test_retrieval_metrics(self):
        retrieved = [["a", "b", "c"], ["d", "e"]]
        references = [["b"], ["f"]]
        m = metrics.compute_retrieval_metrics(retrieved, references)
        self.assertAlmostEqual(m["precision"], (1/3 + 0)/2)
        self.assertAlmostEqual(m["recall"], (1/1 + 0)/2)
        self.assertAlmostEqual(m["mrr"], (1/2 + 0)/2)

    def test_answer_metrics(self):
        preds = ["the cat", "a dog"]
        refs = ["the cat", "dog"]
        m = metrics.compute_answer_metrics(preds, refs)
        self.assertAlmostEqual(m["exact_match"], 0.5)
        self.assertGreater(m["f1"], 0)
        self.assertGreater(m["rouge_l"], 0)

    def test_write_metrics(self):
        with tempfile.TemporaryDirectory() as td:
            metrics.write_metrics("run", "stage", {"a": 1}, metrics_dir=td)
            self.assertTrue(Path(td, "run_stage.json").exists())
            summary = Path(td, "summary.csv").read_text()
            self.assertIn("run,stage,a,1", summary.replace("\n", ""))


if __name__ == "__main__":
    unittest.main()
