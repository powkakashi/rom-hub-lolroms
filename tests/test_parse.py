import importlib.util
import sys
from pathlib import Path

STUB = type(sys)("rom_hub_sdk")


class _P:
    pass


STUB.SearchProvider = _P
STUB.SearchResult = lambda **kw: kw
sys.modules.setdefault("rom_hub_sdk", STUB)

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("lolsearch", ROOT / "lolroms" / "search.py")
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

N64 = "Nintendo/Nintendo 64"
PREFIX = "/Nintendo/Nintendo%2064"
HACKS_DIR = PREFIX + "/Hacks%20%5BReq%20Expansion%20Pack%5D/"


def test_parse_links_keeps_raw_hrefs():
    html = ('<a href="/Pok%C3%A9hacks/Game%20Boy%20Advance/Aesthetic%20Red.7z">x</a>'
            '<a href="/notes.txt">y</a>')
    assert mod.parse_links(html) == ["/Pok%C3%A9hacks/Game%20Boy%20Advance/Aesthetic%20Red.7z"]


def test_is_hack_accepts_hack_folders_and_hack_tags():
    assert mod.is_hack(HACKS_DIR + "Chex%20(World)%20(v0.8.0)%20(Aftermarket)%20(Unl).7z")
    assert mod.is_hack("/Pok%C3%A9hacks/Game%20Boy%20Color/Aesthetic%20Red.7z")
    assert mod.is_hack("/Nintendo/DS/Some%20Game%20(Hack).7z")


def test_is_hack_rejects_retail():
    assert not mod.is_hack("/Nintendo/DS/Team%20Umizoomi%20(Europe).7z")
    assert not mod.is_hack("/Nintendo/Nintendo%2064/Super%20Mario%2064%20(USA).z64.7z")


class _Resp:
    def __init__(self, text):
        self.status_code = 200
        self.text = text


class _Http:
    def __init__(self, pages):
        self.pages = pages

    def get(self, url):
        return _Resp(self.pages.get(url, ""))


class _Ctx:
    def __init__(self):
        self.config = {
            "systems": "n64=" + N64 + ",gba=Nintendo/Game Boy Advance|Pokéhacks/Game Boy Advance",
            "max_rows": "25",
        }
        self.http = _Http(
            {
                "https://lolroms.com/Nintendo/Nintendo%2064/": (
                    '<a href="' + HACKS_DIR.rstrip("/") + '">Hacks</a>'
                    '<a href="/Nintendo/Nintendo%2064/Super%20Mario%2064%20(USA).z64.7z">retail</a>'
                ),
                "https://lolroms.com" + HACKS_DIR: (
                    '<a href="' + HACKS_DIR + 'Chex%20(World)%20(Aftermarket)%20(Unl).7z">Chex</a>'
                ),
            }
        )


def test_search_finds_a_hack_in_the_platform_hack_folder():
    rows = mod.Search(_Ctx()).search("Chex", "n64", 25)
    assert [r["title"] for r in rows] == ["Chex (World) (Aftermarket) (Unl)"]
    assert rows[0]["source_id"].endswith(".7z")


def test_search_does_not_return_retail_files():
    assert mod.Search(_Ctx()).search("Mario", "n64", 25) == []


def test_an_unconfigured_platform_returns_nothing():
    assert mod.Search(_Ctx()).search("Chex", "psx", 25) == []
