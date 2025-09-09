from pathlib import Path
import random

from plugins import PluginLoader
from plugins.cards._base import CardBase

from .party import Party

_loader: PluginLoader | None = None


def _registry() -> dict[str, type[CardBase]]:
    global _loader
    if _loader is None:
        plugin_dir = Path(__file__).resolve().parents[1] / "plugins" / "cards"
        _loader = PluginLoader(required=["card"])
        _loader.discover(str(plugin_dir))
    return _loader.get_plugins("card")


def card_choices(party: Party, stars: int, count: int = 3) -> list[CardBase]:
    cards = [cls() for cls in _registry().values()]
    available = [c for c in cards if c.stars == stars and c.id not in party.cards]
    if not available:
        return []
    return random.sample(available, k=min(count, len(available)))


def award_card(party: Party, card_id: str) -> CardBase | None:
    card_cls = _registry().get(card_id)
    if card_cls is None or card_id in party.cards:
        return None
    party.cards.append(card_id)
    return card_cls()


async def apply_cards(party: Party) -> None:
    registry = _registry()
    for cid in party.cards:
        card_cls = registry.get(cid)
        if card_cls:
            await card_cls().apply(party)
