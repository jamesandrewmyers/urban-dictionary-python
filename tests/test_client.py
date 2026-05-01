from unittest.mock import patch, MagicMock

import pytest

from urban_dictionary import UrbanDictionary


SEARCH_HTML = """
<html><body>
<div aria-label="Pagination"><a aria-label="Last page" href="?term=scag&page=3">3</a></div>
<div class="definition">
  <a class="word">scag</a>
  <div class="meaning">Heroin, you know, the drug?</div>
  <div class="example">Pass me some scag</div>
  <div class="contributor">
    <a href="/define.php?term=scag">scag</a> by <a href="/author.php?author=robbie%20scott">robbie scott</a> April 24, 2003
  </div>
</div>
<div class="definition">
  <a class="word">scag</a>
  <div class="meaning">Second definition</div>
  <div class="example">Another example</div>
  <div class="contributor">
    <a href="/define.php?term=scag">scag</a> by <a href="/author.php?author=someone">someone</a> May 1, 2005
  </div>
</div>
</body></html>
"""

RANDOM_HTML = """
<html><body>
<div class="definition">
  <a class="word">Yeet</a>
  <div class="meaning">To throw something</div>
  <div class="example">I yeeted it</div>
  <div class="contributor">
    <a href="/define.php?term=Yeet">Yeet</a> by <a href="/author.php?author=joe">joe</a> March 1, 2020
  </div>
</div>
</body></html>
"""

BROWSE_HTML = """
<html><body>
<main id="main-content">
<div class="grid">
  <a href="/define.php?term=Aardvark">Aardvark</a>
  <a href="/define.php?term=Abacus">Abacus</a>
  <a href="/define.php?term=Abandon">Abandon</a>
</div>
</main>
</body></html>
"""

AUTHOR_HTML = """
<html><body>
<div class="definition">
  <a class="word">urban</a>
  <div class="meaning">Of the city</div>
  <div class="example">Urban life</div>
  <div class="contributor">
    <a href="/define.php?term=urban">urban</a> by <a href="/author.php?author=Aaron%20Peckham">Aaron Peckham</a> June 1, 2004
  </div>
</div>
</body></html>
"""

EMPTY_HTML = """
<html><body></body></html>
"""


def _mock_get(html):
    mock_resp = MagicMock()
    mock_resp.text = html
    mock_resp.status_code = 200
    return mock_resp


class TestSearch:
    @patch("urban_dictionary.scraper.requests.get")
    def test_returns_definitions(self, mock_get):
        mock_get.return_value = _mock_get(SEARCH_HTML)
        ud = UrbanDictionary()
        result = ud.search("scag", page=1)

        assert result["found"] is True
        assert result["term"] == "scag"
        assert len(result["data"]) == 2
        assert result["total_pages"] == 3

    @patch("urban_dictionary.scraper.requests.get")
    def test_definition_fields(self, mock_get):
        mock_get.return_value = _mock_get(SEARCH_HTML)
        ud = UrbanDictionary()
        entry = ud.search("scag", page=1)["data"][0]

        assert entry["word"] == "scag"
        assert entry["meaning"] == "Heroin, you know, the drug?"
        assert entry["example"] == "Pass me some scag"
        assert entry["contributor"] == "robbie scott"
        assert entry["date"] == "April 24, 2003"

    @patch("urban_dictionary.scraper.requests.get")
    def test_limit(self, mock_get):
        mock_get.return_value = _mock_get(SEARCH_HTML)
        ud = UrbanDictionary()
        result = ud.search("scag", limit=1)

        assert len(result["data"]) == 1

    @patch("urban_dictionary.scraper.requests.get")
    def test_not_found(self, mock_get):
        mock_get.return_value = _mock_get(EMPTY_HTML)
        ud = UrbanDictionary()
        result = ud.search("xyznonexistent", page=1)

        assert result["found"] is False
        assert result["data"] == []


class TestRandom:
    @patch("urban_dictionary.scraper.requests.get")
    def test_returns_definitions(self, mock_get):
        mock_get.return_value = _mock_get(RANDOM_HTML)
        ud = UrbanDictionary()
        result = ud.random(page=1)

        assert result["found"] is True
        assert result["data"][0]["word"] == "Yeet"


class TestBrowse:
    @patch("urban_dictionary.scraper.requests.get")
    def test_returns_word_list(self, mock_get):
        mock_get.return_value = _mock_get(BROWSE_HTML)
        ud = UrbanDictionary()
        result = ud.browse("A", page=1)

        assert result["found"] is True
        assert result["character"] == "A"
        assert result["data"] == ["Aardvark", "Abacus", "Abandon"]

    @patch("urban_dictionary.scraper.requests.get")
    def test_limit(self, mock_get):
        mock_get.return_value = _mock_get(BROWSE_HTML)
        ud = UrbanDictionary()
        result = ud.browse("A", limit=2)

        assert len(result["data"]) == 2


class TestAuthor:
    @patch("urban_dictionary.scraper.requests.get")
    def test_returns_definitions(self, mock_get):
        mock_get.return_value = _mock_get(AUTHOR_HTML)
        ud = UrbanDictionary()
        result = ud.author("Aaron Peckham", page=1)

        assert result["found"] is True
        assert result["author"] == "Aaron Peckham"
        assert result["data"][0]["word"] == "urban"

    @patch("urban_dictionary.scraper.requests.get")
    def test_not_found(self, mock_get):
        mock_get.return_value = _mock_get(EMPTY_HTML)
        ud = UrbanDictionary()
        result = ud.author("nobody12345", page=1)

        assert result["found"] is False
        assert result["data"] == []


class TestCache:
    @patch("urban_dictionary.scraper.requests.get")
    def test_cached_result_avoids_second_request(self, mock_get):
        mock_get.return_value = _mock_get(SEARCH_HTML)
        ud = UrbanDictionary(cache_ttl=300)

        r1 = ud.search("scag", page=1)
        r2 = ud.search("scag", page=1)

        assert r1 == r2
        assert mock_get.call_count == 1

    @patch("urban_dictionary.scraper.requests.get")
    def test_different_params_not_cached(self, mock_get):
        mock_get.return_value = _mock_get(SEARCH_HTML)
        ud = UrbanDictionary(cache_ttl=300)

        ud.search("scag", limit=1)
        ud.search("scag", limit=2)

        assert mock_get.call_count == 2

    @patch("urban_dictionary.scraper.requests.get")
    def test_clear_cache(self, mock_get):
        mock_get.return_value = _mock_get(SEARCH_HTML)
        ud = UrbanDictionary(cache_ttl=300)

        ud.search("scag", page=1)
        ud.clear_cache()
        ud.search("scag", page=1)

        assert mock_get.call_count == 2

    @patch("urban_dictionary.scraper.requests.get")
    def test_no_cache_always_fetches(self, mock_get):
        mock_get.return_value = _mock_get(SEARCH_HTML)
        ud = UrbanDictionary()

        ud.search("scag", page=1)
        ud.search("scag", page=1)

        assert mock_get.call_count == 2


class TestContributorParsing:
    @patch("urban_dictionary.scraper.requests.get")
    def test_two_link_contributor_format(self, mock_get):
        mock_get.return_value = _mock_get(SEARCH_HTML)
        ud = UrbanDictionary()
        entry = ud.search("scag", page=1)["data"][0]

        assert entry["contributor"] == "robbie scott"
        assert entry["date"] == "April 24, 2003"

    @patch("urban_dictionary.scraper.requests.get")
    def test_single_link_contributor_format(self, mock_get):
        html = """
        <html><body>
        <div class="definition">
          <a class="word">test</a>
          <div class="meaning">A test</div>
          <div class="example">Testing</div>
          <div class="contributor">
            <a href="/author.php?author=bob">bob</a> January 1, 2020
          </div>
        </div>
        </body></html>
        """
        mock_get.return_value = _mock_get(html)
        ud = UrbanDictionary()
        entry = ud.search("test", page=1)["data"][0]

        assert entry["contributor"] == "bob"
        assert entry["date"] == "January 1, 2020"
