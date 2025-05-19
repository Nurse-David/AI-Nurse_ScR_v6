import unittest

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


if __name__ == "__main__":
    unittest.main()
