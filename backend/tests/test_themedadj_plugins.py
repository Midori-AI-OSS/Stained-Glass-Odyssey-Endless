import importlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.stats import Stats


def test_themed_adjectives_import_and_decorate() -> None:
    import autofighter.party  # noqa: F401  # Ensure party initializes first

    themedadj = importlib.import_module("plugins.themedadj")
    plugins = themedadj.loader.get_plugins("themedadj")
    assert "atrocious" in plugins

    target = Stats()
    getattr(themedadj, "Atrocious")().apply(target)

    assert target.atk == 220
    assert target.max_hp == 1900
    assert target.get_base_stat("atk") == 220
    assert target.get_base_stat("max_hp") == 1900
    assert not hasattr(target, "_pending_mods")

