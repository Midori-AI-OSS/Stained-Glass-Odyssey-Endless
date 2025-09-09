from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class EmberStone(RelicBase):
    """Burn attacker for 50% ATK when a low-HP ally is struck."""

    id: str = "ember_stone"
    name: str = "Ember Stone"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "Below 25% HP, burn the attacker for 50% ATK per stack."

    def apply(self, party) -> None:
        def _burn(target, attacker, amount) -> None:
            if attacker is None or target not in party.members:
                return
            if target.hp <= target.max_hp * 0.25:
                stacks = party.relics.count(self.id)
                dmg = int(target.atk * 0.5 * stacks)

                # Emit relic effect event for burn counter-attack
                BUS.emit(
                    "relic_effect",
                    "ember_stone",
                    target,
                    "burn_counter",
                    dmg,
                    {
                        "trigger_condition": "below_25_percent_hp",
                        "current_hp_percentage": (target.hp / target.max_hp) * 100,
                        "burn_damage": dmg,
                        "attacker": getattr(attacker, "id", str(attacker)),
                        "stacks": stacks,
                    },
                )

                safe_async_task(attacker.apply_damage(dmg, attacker=target))

        BUS.subscribe("damage_taken", _burn)

    def describe(self, stacks: int) -> str:
        pct = 50 * stacks
        return f"Below 25% HP, burn the attacker for {pct}% ATK."
