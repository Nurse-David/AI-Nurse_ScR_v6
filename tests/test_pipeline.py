import json
import tempfile
import unittest
from pathlib import Path

from ai_nurse_scr import pipeline


class TestPipelineHelpers(unittest.TestCase):
    def test_load_config(self):
        with tempfile.NamedTemporaryFile('w+', suffix='.json', delete=False) as tf:
            json.dump({'pdf_dir': 'data', 'run_id': 'run1'}, tf)
            tf.flush()
            cfg = pipeline.load_config(tf.name)
            self.assertEqual(cfg['pdf_dir'], 'data')
            self.assertEqual(cfg['run_id'], 'run1')

    def test_find_pdfs(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td, 'a.pdf').touch()
            Path(td, 'b.txt').touch()
            pdfs = pipeline.find_pdfs(td)
            self.assertEqual(len(pdfs), 1)
            self.assertTrue(pdfs[0].name == 'a.pdf')

    def test_run_no_pdfs(self):
        with tempfile.TemporaryDirectory() as td, tempfile.NamedTemporaryFile('w+', suffix='.json') as cfg:
            json.dump({'pdf_dir': td, 'run_id': 'run'}, cfg)
            cfg.flush()
            pipeline.run(cfg.name, td)  # should not raise


if __name__ == '__main__':
    unittest.main()
