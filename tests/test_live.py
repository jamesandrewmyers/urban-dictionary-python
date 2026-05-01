"""Live tests that hit Urban Dictionary to verify DOM compatibility.

Run with: pytest tests/test_live.py -v
Skipped by default in CI — pass --run-live or use: pytest -m live
"""

import pytest

from urban_dictionary import UrbanDictionary

pytestmark = pytest.mark.live


DEFINITION_KEYS = {"word", "meaning", "example", "contributor", "date"}


@pytest.fixture(scope="module")
def ud():
    return UrbanDictionary()


class TestSearchLive:
    def test_returns_results(self, ud):
        result = ud.search("hello", page=1, limit=3)

        assert result["found"] is True
        assert len(result["data"]) > 0
        assert "total_pages" in result

    def test_definition_has_expected_fields(self, ud):
        result = ud.search("hello", page=1, limit=1)
        entry = result["data"][0]

        assert set(entry.keys()) == DEFINITION_KEYS
        assert len(entry["word"]) > 0
        assert len(entry["meaning"]) > 0
        assert len(entry["contributor"]) > 0
        assert len(entry["date"]) > 0

    def test_not_found_returns_empty(self, ud):
        result = ud.search("zxqvbnm9999xyznotaword", page=1)

        assert result["found"] is False
        assert result["data"] == []


class TestRandomLive:
    def test_returns_results(self, ud):
        result = ud.random(page=1, limit=2)

        assert result["found"] is True
        assert len(result["data"]) > 0

    def test_definition_has_expected_fields(self, ud):
        result = ud.random(page=1, limit=1)
        entry = result["data"][0]

        assert set(entry.keys()) == DEFINITION_KEYS
        assert len(entry["word"]) > 0
        assert len(entry["meaning"]) > 0


class TestBrowseLive:
    def test_returns_word_list(self, ud):
        result = ud.browse("A", page=1, limit=5)

        assert result["found"] is True
        assert len(result["data"]) > 0
        assert all(isinstance(w, str) for w in result["data"])

    def test_limit_respected(self, ud):
        result = ud.browse("B", page=1, limit=3)

        assert len(result["data"]) <= 3


class TestAuthorLive:
    def test_returns_results(self, ud):
        result = ud.author("Aaron Peckham", page=1, limit=2)

        assert result["found"] is True
        assert len(result["data"]) > 0

    def test_definition_has_expected_fields(self, ud):
        result = ud.author("Aaron Peckham", page=1, limit=1)
        entry = result["data"][0]

        assert set(entry.keys()) == DEFINITION_KEYS
        assert len(entry["contributor"]) > 0
