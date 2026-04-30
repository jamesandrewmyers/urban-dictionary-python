import hashlib
import json

from urban_dictionary.cache import Cache
from urban_dictionary.scraper import scrape_definitions, _yesterday


class UrbanDictionary:
    def __init__(self, cache_ttl=None):
        self._cache = Cache(ttl=cache_ttl) if cache_ttl else None

    def _cache_key(self, method, **kwargs):
        raw = json.dumps({"m": method, **kwargs}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def _cached_call(self, method, callable_, **kwargs):
        if not self._cache:
            return callable_()
        key = self._cache_key(method, **kwargs)
        hit = self._cache.get(key)
        if hit is not None:
            return hit
        result = callable_()
        self._cache.set(key, result)
        return result

    def clear_cache(self):
        if self._cache:
            self._cache.clear()

    def search(self, term, *, strict=False, match_case=False, limit=None,
               page=None, multi_page=None):
        def _call():
            result = scrape_definitions(
                "define.php", "search", term=term, strict=strict,
                match_case=match_case, limit=limit, page=page, multi_page=multi_page,
            )
            result["term"] = term
            return result

        return self._cached_call(
            "search", callable_=_call, term=term, strict=strict,
            match_case=match_case, limit=limit, page=page,
            multi_page=multi_page,
        )

    def random(self, *, limit=None, page=None, multi_page=None):
        def _call():
            return scrape_definitions(
                "random.php", "search", limit=limit, page=page,
                multi_page=multi_page,
            )

        return _call()

    def browse(self, character, *, limit=None, page=None, multi_page=None):
        if character == "new":
            path = "yesterday.php"
            resolved_char = _yesterday()
        else:
            path = "browse.php"
            resolved_char = character

        def _call():
            result = scrape_definitions(
                path, "browse", character=resolved_char, limit=limit,
                page=page, multi_page=multi_page,
            )
            result["character"] = character
            return result

        return self._cached_call(
            "browse", callable_=_call, character=character, limit=limit,
            page=page, multi_page=multi_page,
        )

    def author(self, author, *, term=None, strict=False, match_case=False,
               limit=None, page=None, multi_page=None):
        def _call():
            result = scrape_definitions(
                "author.php", "author", author=author, term=term,
                strict=strict, match_case=match_case, limit=limit,
                page=page, multi_page=multi_page,
            )
            result["author"] = author
            return result

        return self._cached_call(
            "author", callable_=_call, author=author, term=term,
            strict=strict, match_case=match_case, limit=limit,
            page=page, multi_page=multi_page,
        )

    def date(self, date_str, *, limit=None, page=None, multi_page=None):
        # Urban Dictionary has removed yesterday.php — this endpoint
        # will return 404. Kept for forward compatibility if they restore it.
        def _call():
            result = scrape_definitions(
                "yesterday.php", "date", date_str=date_str, limit=limit,
                page=page, multi_page=multi_page,
            )
            result["date"] = date_str
            return result

        return self._cached_call(
            "date", callable_=_call, date_str=date_str, limit=limit,
            page=page, multi_page=multi_page,
        )
