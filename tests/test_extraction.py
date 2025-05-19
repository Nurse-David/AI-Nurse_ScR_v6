import json
import unittest
from unittest.mock import patch, MagicMock
import types
import sys
from pathlib import Path
import tempfile

from ai_nurse_scr import extraction, utils
from ai_nurse_scr.paperqa2.extract import (
    pdfmeta,
    crossref as cr_mod,
    openalex as oa_mod,
    grobid as grobid_mod,
    llm as llm_mod,
)


class TestNormalization(unittest.TestCase):
    def test_normalize_doi(self):
        assert utils.normalize_doi("https://doi.org/10.1000/ABC") == "10.1000/abc"
        assert utils.normalize_doi("10.1000/xyz") == "10.1000/xyz"

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


class TestPaperqaExtractModules(unittest.TestCase):
    @patch("ai_nurse_scr.paperqa2.extract.pdfmeta.extraction.extract_ai_llm_full")
    def test_extract_pdfmeta(self, mock_llm):
        mock_llm.return_value = {"title": "T", "doi": "10.1/xyz"}
        class Dummy:
            def __init__(self):
                self.pages = [types.SimpleNamespace(extract_text=lambda: "text")]
            def __enter__(self):
                return self
            def __exit__(self, exc_type, exc, tb):
                pass

        fake_mod = types.SimpleNamespace(open=lambda p: Dummy())
        with patch.dict(sys.modules, {"pdfplumber": fake_mod}):
            meta = pdfmeta.extract_pdfmeta("file.pdf")
        assert meta["title"] == "T"
        assert "raw_first_page" in meta

    @patch("ai_nurse_scr.paperqa2.extract.crossref.extraction.extract_crossref_full")
    def test_extract_crossref(self, mock_fn):
        mock_fn.return_value = {"title": "t"}
        meta = cr_mod.extract_crossref("10")
        mock_fn.assert_called_with("10")
        assert meta["title"] == "t"

    @patch("ai_nurse_scr.paperqa2.extract.openalex.extraction.extract_openalex_full")
    def test_extract_openalex(self, mock_fn):
        mock_fn.return_value = {"title": "t"}
        meta = oa_mod.extract_openalex("10")
        mock_fn.assert_called_with("10")
        assert meta["title"] == "t"

    @patch("ai_nurse_scr.paperqa2.extract.grobid.check_grobid_healthy", return_value=True)
    def test_extract_grobid(self, mock_health):
        fake_req = types.SimpleNamespace(post=lambda url, files: types.SimpleNamespace(text="xml", raise_for_status=lambda: None))
        with patch.dict(sys.modules, {"requests": fake_req}):
            with tempfile.NamedTemporaryFile(suffix=".pdf") as pdf_file:
                Path(pdf_file.name).touch()
                meta = grobid_mod.extract_grobid(pdf_file.name)
        assert meta["grobid_xml"] == "xml"

    @patch("ai_nurse_scr.paperqa2.extract.llm.extraction.extract_ai_llm_full")
    def test_extract_llm(self, mock_llm):
        mock_llm.return_value = {"title": "t"}
        meta = llm_mod.extract_llm({"raw_first_page": "text"})
        mock_llm.assert_called_with("text")
        assert meta["title"] == "t"

