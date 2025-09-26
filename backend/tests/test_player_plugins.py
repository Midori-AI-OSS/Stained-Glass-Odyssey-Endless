from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from plugins import PluginLoader


def test_player_plugins_import() -> None:
    loader = PluginLoader(required=["player"])
    loader.discover(Path(__file__).resolve().parents[1] / "plugins" / "characters")
    players = loader.get_plugins("player")
    assert "player" in players
