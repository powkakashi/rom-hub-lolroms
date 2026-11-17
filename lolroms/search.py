import re
import urllib.parse

from rom_hub_sdk import SearchProvider, SearchResult

# Directory listing rows: <a href="/Pok%C3%A9hacks/Game%20Boy%20Advance/Aesthetic%20Red.7z">
LINK = re.compile(r'href="(/Pok%C3%A9hacks/[^"]+?\.(?:7z|zip))"', re.I)


def parse_links(html: str) -> list[str]:
    return [urllib.parse.unquote(p) for p in LINK.findall(html or "")]


class Search(SearchProvider):
    def __init__(self, ctx):
        self.ctx = ctx

    def _systems(self) -> dict[str, str]:
        pairs = []
        for chunk in str(self.ctx.config.get("systems") or "").split(","):
            if "=" in chunk:
                pairs.append(chunk.split("=", 1))
        return {k.strip(): v.strip() for k, v in pairs}

    def search(self, query: str, platform: str | None, limit: int) -> list[SearchResult]:
        section = self._systems().get(platform or "")
        if not section or not query.strip():
            return []
        url = "https://lolroms.com/Pok%C3%A9hacks/" + urllib.parse.quote(section)
        resp = self.ctx.http.get(url)
        if resp.status_code != 200:
            return []
        want = query.lower()
        rows = []
        for path in parse_links(resp.text):
            filename = path.rsplit("/", 1)[-1]
            stem = re.sub(r"\.(7z|zip)$", "", filename, flags=re.I)
            if want not in stem.lower():
                continue
            rows.append(
                SearchResult(
                    source_id="https://lolroms.com" + urllib.parse.quote(path),
                    title=stem,
                    platform=platform,
                    extra={"filename": filename, "section": section},
                )
            )
        cap = min(int(self.ctx.config.get("max_rows") or 25), limit)
        return rows[:cap]
