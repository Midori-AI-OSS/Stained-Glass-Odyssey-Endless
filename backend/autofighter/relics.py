from pathlib import Path
import random

from plugins import PluginLoader
from plugins.relics._base import RelicBase

from .party import Party

_loader: PluginLoader | None = None

def _registry() -> dict[str, type[RelicBase]]:
    global _loader
    if _loader is None:
        plugin_dir = Path(__file__).resolve().parents[1] / "plugins" / "relics"
        _loader = PluginLoader(required=["relic"])
        _loader.discover(str(plugin_dir))
    return _loader.get_plugins("relic")

def award_relic(party: Party, relic_id: str) -> RelicBase | None:
    relic_cls = _registry().get(relic_id)
    if relic_cls is None:
        return None
    party.relics.append(relic_id)
    return relic_cls()


def instantiate_relic(relic_id: str) -> RelicBase | None:
    """Return a fresh relic instance without mutating the party."""

    relic_cls = _registry().get(relic_id)
    if relic_cls is None:
        return None
    return relic_cls()


def relic_choices(party: Party, stars: int, count: int = 3) -> list[RelicBase]:
    """Return up to `count` unique relic options for the given star level.

    Ownership is NOT considered here (relics may be offered even if already
    owned). The function avoids duplicate options within a single selection
    batch but may include relics already present in `party.relics`. The special
    fallback relic is excluded here and injected by battle logic only when no
    card options exist.
    """
    relics = [cls() for cls in _registry().values()]
    # Exclude only the fallback essence from normal pools; allow owned relics
    available = [r for r in relics if r.stars == stars and r.id != "fallback_essence"]
    if not available:
        return []
    # Ensure uniqueness within this call
    k = min(count, len(available))
    return random.sample(available, k=k)

async def apply_relics(party: Party) -> None:
    """Apply relic effects to the party.

    Optimized to process each unique relic only once, passing the stack
    count directly to avoid repeated counting.
    """
    registry = _registry()
    # Count stacks for each unique relic upfront
    relic_counts: dict[str, int] = {}
    for rid in party.relics:
        relic_counts[rid] = relic_counts.get(rid, 0) + 1

    # Apply each unique relic once with its stack count
    for rid, stacks in relic_counts.items():
        relic_cls = registry.get(rid)
        if relic_cls:
            relic = relic_cls()
            await relic.apply(party, stacks=stacks)
