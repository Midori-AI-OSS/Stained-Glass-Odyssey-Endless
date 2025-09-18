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

    async def apply(self, party) -> None:
        state = getattr(party, "_ember_stone_state", None)
        stacks = party.relics.count(self.id)

        if state is None:
            async def _burn(target, attacker, amount, *_: object) -> None:
                if attacker is None or target not in party.members:
                    return
                current_stacks = state.get("stacks", 0)
                if current_stacks <= 0:
                    return
                if target.hp <= target.max_hp * 0.25:
                    dmg = int(target.atk * 0.5 * current_stacks)

                    # Emit relic effect event for burn counter-attack
                    await BUS.emit_async("relic_effect", "ember_stone", target, "burn_counter", dmg, {
                        "trigger_condition": "below_25_percent_hp",
                        "current_hp_percentage": (target.hp / target.max_hp) * 100,
                        "burn_damage": dmg,
                        "attacker": getattr(attacker, 'id', str(attacker)),
                        "stacks": current_stacks
                    })

                    safe_async_task(attacker.apply_damage(dmg, attacker=target))

            def _cleanup(*_args) -> None:
                BUS.unsubscribe("damage_taken", state["damage_handler"])
                BUS.unsubscribe("battle_end", state["cleanup_handler"])
                if getattr(party, "_ember_stone_state", None) is state:
                    delattr(party, "_ember_stone_state")

            state = {
                "stacks": stacks,
                "damage_handler": _burn,
                "cleanup_handler": _cleanup,
            }
            party._ember_stone_state = state

            BUS.subscribe("damage_taken", _burn)
            BUS.subscribe("battle_end", _cleanup)
        else:
            state["stacks"] = stacks

    def describe(self, stacks: int) -> str:
        pct = 50 * stacks
        return f"Below 25% HP, burn the attacker for {pct}% ATK."