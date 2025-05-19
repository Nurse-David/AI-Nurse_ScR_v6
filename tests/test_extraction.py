import json
import unittest
from unittest.mock import patch, MagicMock
import types
import sys
from ai_nurse_scr import extraction


class TestNormalization(unittest.TestCase):
    def test_normalize_doi(self):
        assert extraction.normalize_doi("https://doi.org/10.1000/ABC") == "10.1000/abc"
        assert extraction.normalize_doi("10.1000/xyz") == "10.1000/xyz"

    def test_clean_str(self):
        assert extraction.clean_str("A B,C!") == "abc"

    def test_approx_match(self):
        assert extraction.approx_match("https://doi.org/10.1/AAA", "10.1/aaa", "doi")
        assert not extraction.approx_match("10.1/aaa", "10.1/bbb", "doi")
        assert extraction.approx_match("A;B", "B a", "author_keywords")
        assert extraction.approx_match("Title One", "titleone", "title")


class TestCrossref(unittest.TestCase):
    @patch("ai_nurse_scr.extraction.requests")
    def test_extract_crossref_full(self, mock_requests):
        response = {
            "message": {
                "DOI": "10.1234/test",
                "title": ["Test Paper"],
                "author": [{"family": "Doe", "given": "John", "affiliation": [{"name": "USA"}]}],
                "issued": {"date-parts": [[2024]]},
                "subject": ["Nursing"],
                "container-title": ["Journal of Tests"],
                "type": "journal-article",
            }
        }
        mock_requests.get.return_value.json.return_value = response
        meta = extraction.extract_crossref_full("10.1234/test")
        mock_requests.get.assert_called_with("https://api.crossref.org/works/10.1234/test")
        assert meta["doi"] == "10.1234/test"
        assert meta["title"] == "Test Paper"
        assert meta["author"] == "Doe, John"
        assert meta["year"] == "2024"
        assert meta["author_keywords"] == "Nursing"
        assert meta["source_journal"] == "Journal of Tests"
        assert meta["study_type"] == "journal-article"
        assert meta["country"] == "USA"


class TestOpenAlex(unittest.TestCase):
    @patch("ai_nurse_scr.extraction.requests")
    def test_extract_openalex_full(self, mock_requests):
        response = {
            "doi": "https://doi.org/10.1234/test",
            "title": "Test Paper",
            "authorships": [{"author": {"display_name": "John Doe"}, "institutions": [{"country_code": "US"}]}],
            "publication_year": 2024,
            "keywords": ["nursing"],
            "host_venue": {"display_name": "Journal of Tests"},
            "type": "journal-article",
        }
        mock_requests.get.return_value.json.return_value = response
        meta = extraction.extract_openalex_full("10.1234/test")
        mock_requests.get.assert_called_with(
            "https://api.openalex.org/works/https://doi.org/10.1234/test"
        )
        assert meta["doi"] == "10.1234/test"
        assert meta["title"] == "Test Paper"
        assert meta["author"] == "John Doe"
        assert meta["year"] == "2024"
        assert meta["author_keywords"] == "nursing"
        assert meta["source_journal"] == "Journal of Tests"
        assert meta["study_type"] == "journal-article"
        assert meta["country"] == "US"


class TestOpenAI(unittest.TestCase):
    def _mock_openai(self, content):
        mock_resp = MagicMock()
        mock_resp.choices = [MagicMock(message=MagicMock(content=content))]
        return types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=MagicMock(return_value=mock_resp))))

    def test_extract_ai_llm_doi_only(self):
        mock_openai = self._mock_openai('{"doi":"10.1234/test"}')
        with patch.dict(sys.modules, {"openai": mock_openai}):
            result = extraction.extract_ai_llm_doi_only("some text", api_key="key")
        assert result == "10.1234/test"

    def test_extract_ai_llm_full(self):
        payload = {
            "title": "Test Paper",
            "author": "Doe, John",
            "year": "2024",
            "doi": "10.1234/test",
            "author_keywords": "nursing",
            "country": "US",
            "source_journal": "Journal of Tests",
            "study_type": "journal-article",
        }
        mock_openai = self._mock_openai(json.dumps(payload))
        with patch.dict(sys.modules, {"openai": mock_openai}):
            meta = extraction.extract_ai_llm_full("text", api_key="key")
        assert meta == payload
