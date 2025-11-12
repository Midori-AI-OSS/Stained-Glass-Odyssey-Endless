from dataclasses import dataclass
from dataclasses import field
import random

from autofighter.stats import BUS
from plugins.effects.aftertaste import Aftertaste
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class PlagueHarp(RelicBase):
    """Echo party DoTs into other foes at the cost of caster HP."""

    id: str = "plague_harp"
    name: str = "Plague Harp"
    stars: int = 3
    effects: dict[str, float] = field(default_factory=dict)
    full_about: str = (
        "When allies' DoTs tick, echo 40% of the damage to another foe per stack, "
        "and the caster loses 2% of their Max HP per stack."
    )
    summarized_about: str = (
        "Echoes damage from DoTs to other foes but drains caster HP"
    )

    async def apply(self, party) -> None:
        await super().apply(party)

        stacks = max(int(party.relics.count(self.id)), 0)
        state = getattr(party, "_plague_harp_state", None)

        if state is None:
            state = {
                "stacks": stacks,
                "foes": [],
                "rng": random.Random(),
            }
            party._plague_harp_state = state
        else:
            state["stacks"] = stacks
            foes = [foe for foe in state.get("foes", []) if getattr(foe, "hp", 0) > 0]
            state["foes"] = foes
            if "rng" not in state or not isinstance(state["rng"], random.Random):
                state["rng"] = random.Random()

        async def _on_turn_start(entity) -> None:
            from plugins.characters.foe_base import FoeBase

            current_state = getattr(party, "_plague_harp_state", state)
            foes = current_state.setdefault("foes", [])

            if entity is None or not isinstance(entity, FoeBase):
                return

            if getattr(entity, "hp", 0) > 0 and entity not in foes:
                foes.append(entity)

            current_state["foes"] = [foe for foe in foes if getattr(foe, "hp", 0) > 0]

        async def _on_dot_tick(attacker, target, amount, dot_name, metadata=None) -> None:
            from plugins.characters.foe_base import FoeBase

            if attacker is None or target is None or amount is None:
                return

            if attacker not in getattr(party, "members", ()):  # type: ignore[arg-type]
                return

            if not isinstance(target, FoeBase):
                return

            if amount <= 0:
                return

            if getattr(attacker, "hp", 0) <= 0:
                return

            current_state = getattr(party, "_plague_harp_state", state)
            current_stacks = max(int(current_state.get("stacks", 0)), 0)
            if current_stacks <= 0:
                return

            foes = [foe for foe in current_state.get("foes", []) if getattr(foe, "hp", 0) > 0]
            if getattr(target, "hp", 0) > 0 and target not in foes:
                foes.append(target)

            if not foes:
                return

            rng = current_state.get("rng")
            if not isinstance(rng, random.Random):
                rng = random.Random()
                current_state["rng"] = rng

            alternatives = [foe for foe in foes if foe is not target and getattr(foe, "hp", 0) > 0]
            if alternatives:
                echo_target = rng.choice(alternatives)
            else:
                echo_target = target

            base_damage = max(1, int(amount * 0.4 * current_stacks))

            await BUS.emit_async(
                "relic_effect",
                self.id,
                echo_target,
                "dot_echo",
                base_damage,
                {
                    "dot_name": dot_name,
                    "dot_damage": amount,
                    "echo_base_damage": base_damage,
                    "foe": getattr(echo_target, "id", "unknown"),
                    "original_target": getattr(target, "id", "unknown"),
                    "stacks": current_stacks,
                },
                attacker,
            )

            aftertaste = Aftertaste(base_pot=base_damage)
            safe_async_task(aftertaste.apply(attacker, echo_target))

            max_hp = getattr(attacker, "max_hp", 0)
            tithe = max(1, int(max_hp * 0.02 * current_stacks)) if max_hp else 0
            if tithe > 0 and getattr(attacker, "hp", 0) > 0:
                safe_async_task(attacker.apply_cost_damage(tithe))
                await BUS.emit_async(
                    "relic_effect",
                    self.id,
                    attacker,
                    "health_tithe",
                    tithe,
                    {
                        "tithe_percentage": 2 * current_stacks,
                        "max_hp": max_hp,
                        "dot_name": dot_name,
                        "stacks": current_stacks,
                    },
                )

        def _cleanup(*_args) -> None:
            self.clear_subscriptions(party)
            current_state = getattr(party, "_plague_harp_state", None)
            if isinstance(current_state, dict):
                current_state.get("foes", []).clear()
                if current_state is state:
                    delattr(party, "_plague_harp_state")

        self.subscribe(party, "turn_start", _on_turn_start)
        self.subscribe(party, "dot_tick", _on_dot_tick)
        self.subscribe(party, "battle_end", _cleanup)

    def full_about_stacks(self, stacks: int) -> str:
        """Provide stack-aware description."""
        return self.describe(stacks)

    def describe(self, stacks: int) -> str:
        echo_pct = 40 * stacks
        tithe_pct = 2 * stacks
        return (
            "When allies' DoTs tick, echo "
            f"{echo_pct}% of the damage to another foe if possible, and the caster loses "
            f"{tithe_pct}% of their Max HP."
        )
