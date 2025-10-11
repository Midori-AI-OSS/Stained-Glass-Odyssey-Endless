from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase


@dataclass
class StellarCompass(RelicBase):
    """Critical hits grant permanent +1.5% ATK and gold rate."""

    id: str = "stellar_compass"
    name: str = "Stellar Compass"
    stars: int = 3
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "Critical hits grant permanent +1.5% ATK and gold rate."

    async def apply(self, party) -> None:
        await super().apply(party)

        state = getattr(party, "_stellar_compass_state", None)
        if state is None:
            state = {"gold": 0.0, "crits": {}}
            party._stellar_compass_state = state

        async def _crit(attacker, target, damage, *_):
            if attacker not in party.members:
                return
            current_state = getattr(party, "_stellar_compass_state", state)
            copies = party.relics.count(self.id)
            attacker_id = getattr(attacker, "id", id(attacker))
            crits = current_state["crits"].get(attacker_id, 0) + 1
            current_state["crits"][attacker_id] = crits

            atk_mult = 1 + 0.015 * crits * copies
            mod_name = f"{self.id}_crit_{attacker_id}"
            attacker.remove_effect_by_name(mod_name)
            mod = create_stat_buff(
                attacker,
                name=mod_name,
                atk_mult=atk_mult,
                turns=9999,
            )
            await attacker.effect_manager.add_modifier(mod)
            current_state["gold"] += 0.015 * copies

            # Track critical hit buff application
            await BUS.emit_async(
                "relic_effect",
                "stellar_compass",
                attacker,
                "crit_buff_applied",
                damage,
                {
                    "target": getattr(target, "id", str(target)),
                    "atk_boost_percentage": 1.5 * copies,
                    "total_atk_boost": 1.5 * copies * crits,
                    "gold_rate_increase": 1.5 * copies,
                    "total_gold_rate": current_state["gold"] * 100,
                    "stacks": copies,
                    "crit_count": crits,
                    "permanent": True,
                },
            )

        async def _gold(amount: int) -> None:
            current_state = getattr(party, "_stellar_compass_state", state)
            if current_state["gold"] > 0:
                bonus_gold = int(amount * current_state["gold"])
                party.gold += bonus_gold

                # Track bonus gold generation
                await BUS.emit_async(
                    "relic_effect",
                    "stellar_compass",
                    party,
                    "bonus_gold_earned",
                    bonus_gold,
                    {
                        "base_gold": amount,
                        "gold_rate_multiplier": current_state["gold"],
                        "total_crits_accumulated": sum(current_state["crits"].values()),
                    },
                )

        self.subscribe(party, "critical_hit", _crit)
        self.subscribe(party, "gold_earned", _gold)

    def describe(self, stacks: int) -> str:
        bonus = 1.5 * stacks
        return (
            f"Critical hits grant permanent +{bonus:.1f}% ATK and gold gain."
        )
