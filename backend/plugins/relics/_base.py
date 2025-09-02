import asyncio
from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.party import Party

log = logging.getLogger(__name__)


def safe_async_task(coro):
    """Safely create an async task, handling cases where no event loop is running."""
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        return loop.create_task(coro)
    except RuntimeError:
        # No event loop running, create a new one and run the coroutine
        try:
            return asyncio.run(coro)
        except Exception as e:
            log.warning("Failed to execute async operation: %s", e)
            return None


@dataclass
class RelicBase:
    plugin_type = "relic"

    id: str = ""
    name: str = ""
    stars: int = 1
    effects: dict[str, float] = field(default_factory=dict)
    about: str = ""

    def apply(self, party: Party) -> None:
        from autofighter.stats import BUS  # Import here to avoid circular imports

        log.info("Applying relic %s to party", self.id)
        mods = []
        stacks = party.relics.count(self.id)

        for member in party.members:
            log.debug("Applying relic to %s", getattr(member, "id", "member"))
            mgr = getattr(member, "effect_manager", None)
            if mgr is None:
                mgr = EffectManager(member)
                member.effect_manager = mgr

            # Apply stack multiplier to effects: each additional copy multiplies the effect
            changes = {f"{attr}_mult": (1 + pct) ** stacks for attr, pct in self.effects.items()}
            if not changes:
                continue
            mod = create_stat_buff(member, name=self.id, turns=9999, bypass_diminishing_returns=True, **changes)
            mgr.add_modifier(mod)
            mods.append(mod)

            # Emit relic effect tracking for stat modifications
            for attr, pct in self.effects.items():
                BUS.emit("relic_effect", self.id, member, f"stat_buff_{attr}", int(pct * 100), {
                    "stat_affected": attr,
                    "percentage_change": pct * 100,
                    "stacks": stacks,
                    "cumulative_effect": (1 + pct) ** stacks - 1 if stacks > 1 else pct,
                    "modifier_name": self.id
                })

        self._mods = mods

    def remove(self) -> None:
        for mod in getattr(self, "_mods", []):
            mod.remove()
        self._mods = []

    def describe(self, stacks: int) -> str:
        return self.about
