"""LoLSuite search across a platform's hack folders — not only the Pokéhacks sections.

The site publishes per-platform directories, and hacks live either in a `Hacks …` subdirectory
(N64: `Nintendo/Nintendo 64/Hacks [Req Expansion Pack]/`) or inline with a `(Hack)` tag, plus the
older `/Pokéhacks/<system>` sections. A search limited to Pokéhacks saw almost none of that:
measured 2026-11-20, today's RSS carried 3 N64 hack files and only 2 Pokéhacks entries.
"""

import re
import urllib.parse

from rom_hub_sdk import SearchProvider, SearchResult

BASE = "https://lolroms.com"
FILE = re.compile(r'href="([^"]+?\.(?:7z|zip))"', re.IGNORECASE)
DIR = re.compile(r'href="([^"]+)"', re.IGNORECASE)
HACK = re.compile(r"hack", re.IGNORECASE)


def parse_links(html: str) -> list[str]:
    """Raw (percent-encoded) file hrefs, root-relative."""
    return [p for p in FILE.findall(html or "") if p.startswith("/")]


def parse_dirs(html: str) -> list[str]:
    """Child-directory hrefs. The site writes them without a trailing slash (`…/Hacks%20[…]`)."""
    return [
        p
        for p in DIR.findall(html or "")
        if p.startswith("/") and "." not in p.rsplit("/", 1)[-1]
    ]


def decoded(path: str) -> str:
    return urllib.parse.unquote(path)


def is_hack(path: str) -> bool:
    """True when a directory on the path names hacks, or the filename carries (Hack)."""
    parts = [decoded(p) for p in path.split("/") if p]
    if not parts:
        return False
    return any(HACK.search(p) for p in parts[:-1]) or "(hack)" in parts[-1].lower()


class Search(SearchProvider):
    def __init__(self, ctx):
        self.ctx = ctx

    def _sections(self) -> dict[str, list[str]]:
        """platform -> section paths. `|` separates the platform's own dir from Pokéhacks."""
        out: dict[str, list[str]] = {}
        for chunk in str(self.ctx.config.get("systems") or "").split(","):
            key, _, value = chunk.partition("=")
            if not key.strip() or not value.strip():
                continue
            out[key.strip()] = [s.strip() for s in value.split("|") if s.strip()]
        return out

    def _listing(self, section: str) -> list[str]:
        """File links from the section listing plus its hack-named subdirectories."""
        prefix = "/" + urllib.parse.quote(section, safe="/")
        resp = self.ctx.http.get(f"{BASE}{prefix}/")
        if resp.status_code != 200:
            return []
        links = parse_links(resp.text)
        for sub in parse_dirs(resp.text):
            if not sub.startswith(prefix + "/"):
                continue  # nav link, not a child of this section
            name = decoded(sub.rstrip("/").rsplit("/", 1)[-1])
            if not (HACK.search(name) or HACK.search(section)):
                continue
            child = self.ctx.http.get((BASE + sub).rstrip("/") + "/")
            if child.status_code == 200:
                links += parse_links(child.text)
        return links

    def search(self, query: str, platform: str | None, limit: int) -> list[SearchResult]:
        sections = self._sections().get(platform or "", [])
        if not sections or not query.strip():
            return []
        want = query.lower()
        scope = str(self.ctx.config.get("include") or "all").strip().lower()
        rows: list[SearchResult] = []
        seen: set[str] = set()
        for section in sections:
            for path in self._listing(section):
                hack = is_hack(path)
                if path in seen or (scope == "hacks" and not hack) or (scope == "retail" and hack):
                    continue
                seen.add(path)
                filename = decoded(path.rsplit("/", 1)[-1])
                stem = re.sub(r"\.(7z|zip)$", "", filename, flags=re.IGNORECASE)
                if want not in stem.lower():
                    continue
                rows.append(
                    SearchResult(
                        source_id=BASE + path,
                        title=stem,
                        platform=platform,
                        extra={"filename": filename, "section": section},
                    )
                )
        cap = min(int(self.ctx.config.get("max_rows") or 25), limit)
        return rows[:cap]
