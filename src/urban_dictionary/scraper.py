import re

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.urbandictionary.com"


def _extract_details(definition_el):
    word_el = definition_el.select_one(".word")
    meaning_el = definition_el.select_one(".meaning")
    example_el = definition_el.select_one(".example")
    contributor_el = definition_el.select_one(".contributor")

    contributor = ""
    entry_date = ""
    if contributor_el:
        links = contributor_el.find_all("a")
        if len(links) > 1:
            contributor = links[1].get_text(strip=True)
        elif links:
            contributor = links[0].get_text(strip=True)

        text_nodes = [
            node for node in contributor_el.children
            if isinstance(node, str) and node.strip()
        ]
        if text_nodes:
            entry_date = text_nodes[-1].strip()

    return {
        "word": word_el.get_text(strip=True) if word_el else "",
        "meaning": meaning_el.get_text(strip=True) if meaning_el else "",
        "example": example_el.get_text(strip=True) if example_el else "",
        "contributor": contributor,
        "date": entry_date,
    }


def _extract_word_list(soup):
    main_el = soup.select_one("main")
    if not main_el:
        return []

    # New layout: grid of <a> tags inside main
    grid = main_el.select_one("div.grid")
    if grid:
        return [a.get_text(strip=True) for a in grid.select("a") if a.get_text(strip=True)]

    # Legacy layout: <ul>/<li> inside main
    items = main_el.select("ul:first-of-type > li")
    return [li.select_one("a").get_text() for li in items if li.select_one("a")]


def _build_url(path, scrape_type, *, term=None, author=None, character=None):
    url = f"{BASE_URL}/{path}"
    if scrape_type == "search" and term:
        url += f"?term={requests.utils.quote(term)}"
    elif scrape_type == "browse":
        if re.match(r"^\d{4}-\d{2}-\d{2}$", character or ""):
            url += f"?date={character}"
        else:
            url += f"?character={requests.utils.quote(character or '')}"
    elif scrape_type == "author" and author:
        url += f"?author={requests.utils.quote(author)}"
    return url


def _get_soup(url):
    resp = requests.get(url, timeout=15)
    return BeautifulSoup(resp.text, "html.parser")


def _get_total_pages(soup):
    last_link = soup.select_one("div[aria-label='Pagination'] a[aria-label='Last page']")
    if last_link and last_link.get("href"):
        match = re.search(r"page=(\d+)", last_link["href"])
        if match:
            return int(match.group(1))
    return 1


def _resolve_pages(page, multi_page):
    if page is not None:
        if multi_page:
            start, end = multi_page
            return start, end
        return page, page

    if multi_page:
        return multi_page
    return 1, 5


def scrape_definitions(path, scrape_type="search", *, term=None, author=None,
                       character=None, strict=False,
                       match_case=False, limit=None, page=None, multi_page=None):
    url = _build_url(path, scrape_type, term=term, author=author,
                     character=character)
    soup = _get_soup(url)

    definitions = soup.select(".definition")

    if scrape_type == "search" and not definitions:
        return {"found": False, "data": []}
    if scrape_type == "author" and not definitions:
        return {"found": False, "data": []}

    if scrape_type == "search" and path != "random.php" and definitions:
        first_word = definitions[0].select_one(".word")
        first_word_text = first_word.get_text() if first_word else ""
        if first_word_text != (term or "") and match_case:
            return {"found": False, "data": []}
        elif first_word_text != (term or ""):
            term = first_word_text

    current_page, max_page = _resolve_pages(page, multi_page)
    total_pages = _get_total_pages(soup)

    results = []
    break_loop = False

    while current_page <= max_page:
        if current_page > 1:
            page_url = _build_url(path, scrape_type, term=term, author=author,
                                  character=character)
            page_url += f"&page={current_page}"
            soup = _get_soup(page_url)

        if scrape_type in ("search", "author"):
            for el in soup.select(".definition"):
                entry = _extract_details(el)

                if scrape_type == "author" and strict:
                    if entry["word"].lower() != (term or "").lower():
                        continue
                elif scrape_type == "author" and match_case:
                    if entry["word"] != (term or ""):
                        continue

                results.append(entry)
                if limit and len(results) >= limit:
                    break_loop = True
                    break

        elif scrape_type == "browse":
            words = _extract_word_list(soup)

            for word in words:
                results.append(word)
                if limit and len(results) >= limit:
                    break_loop = True
                    break

        if break_loop:
            break

        current_page += 1

    return {
        "found": len(results) > 0,
        "total_pages": total_pages,
        "data": results,
    }
