from dataclasses import dataclass
from dataclasses import field
import random

from autofighter.stats import BUS
from plugins.effects.aftertaste import Aftertaste
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class RustyBuckle(RelicBase):
    """Bleeds lowest-HP ally and triggers Aftertaste as HP drops."""

    id: str = "rusty_buckle"
    name: str = "Rusty Buckle"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=dict)
    about: str = (
        "Bleeds the weakest ally and unleashes growing Aftertaste blasts as they suffer."
    )

    def apply(self, party) -> None:
        """Bleed weakest ally and ping foes as their HP drops."""
        super().apply(party)

        stacks = party.relics.count(self.id)
        state: dict[str, object] = {"foes": [], "ally": None, "triggers": 0}

        def _battle_start(entity) -> None:
            from plugins.foes._base import FoeBase

            if isinstance(entity, FoeBase):
                state["foes"].append(entity)
                return

            if state["ally"] is None and party.members:
                ally = min(party.members, key=lambda m: m.max_hp)
                # Increase initial bleed to 5% per stack (was 1%)
                bleed = int(ally.max_hp * 0.05 * stacks)
                dmg = min(bleed, max(ally.hp - 1, 0))

                # Emit relic effect event for initial bleed
                BUS.emit(
                    "relic_effect",
                    "rusty_buckle",
                    ally,
                    "initial_bleed",
                    dmg,
                    {
                        "target_selection": "lowest_max_hp",
                        "bleed_percentage": 5 * stacks,
                        "stacks": stacks,
                    },
                )

                safe_async_task(ally.apply_damage(dmg, attacker=ally))
                state["ally"] = ally
                state["triggers"] = 0

        def _damage(target, attacker, amount) -> None:
            ally = state.get("ally")
            if target is not ally:
                return
            max_hp = ally.max_hp
            triggers = state["triggers"]
            lost_frac = 1 - (ally.hp / max_hp)
            while lost_frac >= 0.1 * (triggers + 1):
                triggers += 1
                state["triggers"] = triggers
                total_lost = max_hp * 0.1 * triggers
                dmg = int(total_lost * 0.005)
                hits = 5 + 3 * (stacks - 1)

                # Emit relic effect event for aftertaste trigger
                BUS.emit(
                    "relic_effect",
                    "rusty_buckle",
                    ally,
                    "aftertaste_trigger",
                    dmg,
                    {
                        "trigger_count": triggers,
                        "hp_lost_percentage": lost_frac * 100,
                        "aftertaste_hits": hits,
                        "damage_per_hit": dmg,
                    },
                )

                for _ in range(hits):
                    if state["foes"]:
                        foe = random.choice(state["foes"])
                        safe_async_task(Aftertaste(base_pot=dmg).apply(ally, foe))

        BUS.subscribe("battle_start", _battle_start)
        BUS.subscribe("damage_taken", _damage)

    def describe(self, stacks: int) -> str:
        bleed = 5 * stacks
        hits = 5 + 3 * (stacks - 1)
        return (
            f"Lowest-HP ally bleeds for {bleed}% Max HP at start. "
            f"Each 10% HP lost triggers {hits} Aftertaste hits at random foes."
        )
