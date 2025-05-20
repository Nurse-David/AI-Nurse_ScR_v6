import json
try:
    import yaml
except Exception:
    yaml = None
import tempfile
import unittest
from pathlib import Path
import sys

from ai_nurse_scr import pipeline, config as config_mod
from unittest.mock import patch
import types


class TestPipelineHelpers(unittest.TestCase):
    def test_load_config(self):
        with tempfile.NamedTemporaryFile('w+', suffix='.json') as tf:
            json.dump({'pdf_dir': 'data', 'run_id': 'run1'}, tf)
            tf.flush()
            cfg = config_mod.load_config(tf.name)
            self.assertEqual(cfg.pdf_dir, 'data')
            self.assertEqual(cfg.run_id, 'run1')

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

    def test_extract_text(self):
        class Dummy:
            def __init__(self):
                self.pages = [types.SimpleNamespace(extract_text=lambda: "Hello World")]
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                pass

        fake_mod = types.SimpleNamespace(open=lambda path: Dummy())
        with patch.dict(sys.modules, {"pdfplumber": fake_mod}):
            text = pipeline.extract_text(Path("test.pdf"))
        self.assertIn("Hello World", text)

    @patch("ai_nurse_scr.pipeline.extraction.extract_openalex_full")
    @patch("ai_nurse_scr.pipeline.extraction.extract_crossref_full")
    @patch("ai_nurse_scr.pipeline.extraction.extract_ai_llm_full")
    def test_extract_data(self, mock_llm, mock_cr, mock_oa):
        mock_llm.return_value = {"doi": "10.1/test", "title": "A"}
        mock_cr.return_value = {"year": "2024"}
        mock_oa.return_value = {"author": "Doe"}
        data = pipeline.extract_data("text")
        self.assertEqual(data["doi"], "10.1/test")
        self.assertEqual(data["year"], "2024")
        self.assertEqual(data["author"], "Doe")

    @patch("ai_nurse_scr.pipeline.extract_data")
    @patch("ai_nurse_scr.pipeline.extract_text")
    def test_run_writes_output(self, mock_text, mock_data):
        mock_text.return_value = "text"
        mock_data.return_value = {"title": "T"}
        with tempfile.TemporaryDirectory() as td, tempfile.NamedTemporaryFile('w+', suffix='.json') as cfg:
            json.dump({'pdf_dir': td, 'run_id': 'run', 'output_dir': td}, cfg)
            cfg.flush()
            Path(td, 'doc.pdf').touch()
            pipeline.run(cfg.name, td, force=True)
            meta_files = list(Path(td).glob('run_metadata_*.jsonl'))
            self.assertTrue(meta_files)
            
            metrics_dir = Path('outputs/metrics')
            summary = metrics_dir / 'summary.csv'
            self.assertTrue(summary.exists())
            snapshot = Path(td) / 'config_snapshot.yaml'
            self.assertTrue(snapshot.exists())
            with open(snapshot) as sf:
                snap = yaml.safe_load(sf) if yaml else json.load(sf)
            self.assertEqual(snap['pdf_dir'], td)

            run_info = Path(td) / 'run_info.yaml'
            self.assertTrue(run_info.exists())
            with open(run_info) as rf:
                info = yaml.safe_load(rf) if yaml else json.load(rf)
            self.assertIn('pipeline_version', info)
            self.assertIn('git_hash', info)

    @patch("ai_nurse_scr.pipeline.ask_llm")
    @patch("ai_nurse_scr.pipeline.extract_text")
    def test_run_rounds_outputs(self, mock_text, mock_llm):
        mock_text.return_value = "content" * 5
        mock_llm.return_value = "answer"
        with tempfile.TemporaryDirectory() as td, tempfile.NamedTemporaryFile('w+', suffix='.json') as cfg:
            json.dump({
                'pdf_dir': td,
                'run_id': 'run',
                'output_dir': td,
                'rounds': {
                    'question': 'Q?',
                    'chunk_size': 5,
                    'round1': {'top_n': 1, 'temperature': 0.5},
                    'round2': {'temperature': 0}
                }
            }, cfg)
            cfg.flush()
            Path(td, 'doc.pdf').touch()
            pipeline.run_rounds(cfg.name, td, force=True)
            out1 = list(Path(td).glob('run_round1_*.jsonl'))
            out2 = list(Path(td).glob('run_round2_*.jsonl'))
            self.assertTrue(out1)
            self.assertTrue(out2)

    @patch("ai_nurse_scr.pipeline.extract_data")
    @patch("ai_nurse_scr.pipeline.extract_text")
    def test_run_multiple(self, mock_text, mock_data):
        mock_text.return_value = "text"
        mock_data.return_value = {"title": "T"}
        with tempfile.TemporaryDirectory() as td, tempfile.NamedTemporaryFile('w+', suffix='.json') as cfg:
            json.dump({'pdf_dir': td, 'run_id': 'run', 'output_dir': td}, cfg)
            cfg.flush()
            Path(td, 'doc.pdf').touch()
            outputs = pipeline.run_multiple(cfg.name, td, rounds=2)
            self.assertEqual(len(outputs), 2)
            self.assertTrue(all(p.exists() for p in outputs))


if __name__ == '__main__':
    unittest.main()
