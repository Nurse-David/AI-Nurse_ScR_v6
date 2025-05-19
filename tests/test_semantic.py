import tempfile
import types
from pathlib import Path

import unittest
from unittest.mock import patch
import sys

from ai_nurse_scr.evaluation import llm_semantic_compare, spotcheck_files


class DummyResp:
    def __init__(self, content="Yes"):
        self.choices = [types.SimpleNamespace(message=types.SimpleNamespace(content=content))]


class DummyClient:
    def __init__(self, *args, **kwargs):
        pass

    class chat:
        class completions:
            @staticmethod
            def create(*args, **kwargs):
                return DummyResp()


class TestSemantic(unittest.TestCase):
    def _patch_openai(self):
        fake = types.SimpleNamespace(OpenAI=lambda *a, **k: DummyClient())
        return patch.dict(sys.modules, {"openai": fake})

    def test_llm_semantic_compare(self):
        with self._patch_openai() as _:
            verdict = llm_semantic_compare("ctx", "a1", "a2", openai_api_key="key")
        self.assertEqual(verdict, "Yes")

    def test_spotcheck_files(self):
        with self._patch_openai() as _:
            with tempfile.TemporaryDirectory() as td:
                f1 = Path(td) / "a.csv"
                f2 = Path(td) / "b.csv"
                with open(f1, "w", newline="", encoding="utf-8") as f:
                    f.write("text,llm_answer\nctx,a\n")
                with open(f2, "w", newline="", encoding="utf-8") as f:
                    f.write("text,llm_answer\nctx,a\n")
                out = spotcheck_files(f1, f2, n_check=1, openai_api_key="key")
                with open(out) as f:
                    lines = f.readlines()
                self.assertEqual(len(lines), 2)
                self.assertIn("verdict", lines[0])
                self.assertIn("Yes", lines[1])


if __name__ == "__main__":
    unittest.main()


