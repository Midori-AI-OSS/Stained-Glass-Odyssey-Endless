from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.stats import Stats
from plugins.themedadj import Atrocious
from plugins.themedadj import loader


def test_themed_adjectives_import_and_decorate() -> None:
    plugins = loader.get_plugins("themedadj")
    assert "atrocious" in plugins

    target = Stats()
    Atrocious().apply(target)

    assert target.atk == 220
    assert target.max_hp == 1900
    assert hasattr(target, "_pending_mods")
    mod = target._pending_mods[0]
    assert mod.multipliers["atk"] == 1.1
    assert mod.multipliers["max_hp"] == 1.9
