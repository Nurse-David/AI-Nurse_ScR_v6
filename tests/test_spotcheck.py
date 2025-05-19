import unittest
from unittest.mock import MagicMock
import types
import sys

from ai_nurse_scr.spotcheck import semantic_spot_check


class TestSpotCheck(unittest.TestCase):
    def _mock_openai(self, reply: str):
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content=reply))]
        return types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=MagicMock(return_value=mock_resp))))

    def test_semantic_yes(self):
        mock_openai = self._mock_openai("Yes")
        with unittest.mock.patch.dict(sys.modules, {"openai": mock_openai}):
            self.assertTrue(semantic_spot_check("a", "b", api_key="k"))

    def test_semantic_no(self):
        mock_openai = self._mock_openai("No")
        with unittest.mock.patch.dict(sys.modules, {"openai": mock_openai}):
            self.assertFalse(semantic_spot_check("a", "b", api_key="k"))


if __name__ == "__main__":
    unittest.main()
