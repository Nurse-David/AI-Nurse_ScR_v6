import json
import tempfile
from pathlib import Path
from unittest.mock import patch
import unittest
try:
    import yaml
except Exception:
    yaml = None

from ai_nurse_scr import pipeline

class TestFullPipeline(unittest.TestCase):
    @patch("ai_nurse_scr.pipeline.ask_llm", return_value="ans")
    @patch("ai_nurse_scr.pipeline.extract_data", return_value={"title": "T"})
    @patch("ai_nurse_scr.pipeline.extract_text", return_value="text")
    def test_full_pipeline(self, m_text, m_data, m_llm):
        with tempfile.TemporaryDirectory() as td:
            pdf = Path(td) / "d.pdf"
            pdf.touch()
            ext = ".yaml" if yaml else ".json"
            cfg_path = Path(td) / f"cfg{ext}"
            cfg = {
                "pdf_dir": td,
                "run_id": "run",
                "output_dir": td,
                "rounds": {
                    "question": "Q?",
                    "chunk_size": 5,
                    "round1": {"top_n": 1},
                    "round2": {},
                },
            }
            with open(cfg_path, "w", encoding="utf-8") as f:
                if yaml:
                    yaml.safe_dump(cfg, f)
                else:
                    json.dump(cfg, f)

            meta = pipeline.run(str(cfg_path), td, force=True)
            r1, r2 = pipeline.run_rounds(str(cfg_path), td, force=True)

            self.assertTrue(meta.exists())
            self.assertTrue(r1.exists())
            self.assertTrue(r2.exists())
            self.assertTrue((Path(td) / "run_info.yaml").exists())
            self.assertTrue((Path(td) / "config_snapshot.yaml").exists())

if __name__ == "__main__":
    unittest.main()
