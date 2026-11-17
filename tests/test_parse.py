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


def test_parse_links_decodes_and_keeps_hack_files_only():
    html = ('<a href="/Pok%C3%A9hacks/Game%20Boy%20Advance/Aesthetic%20Red.7z">x</a>'
            '<a href="/Pok%C3%A9hacks/Game%20Boy%20Advance/notes.txt">y</a>')
    assert mod.parse_links(html) == ["/Pokéhacks/Game Boy Advance/Aesthetic Red.7z"]
