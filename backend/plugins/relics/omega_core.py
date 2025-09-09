"""Omega Core relic effects."""

from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class OmegaCore(RelicBase):
    """Huge stat surge for a short time, then escalating HP drain."""

    id: str = "omega_core"
    name: str = "Omega Core"
    stars: int = 5
    effects: dict[str, float] = field(
        default_factory=lambda: {"atk": 6.0, "defense": 6.0}
    )
    about: str = (
        "Multiplies all stats for the entire fight before draining ally health."
    )

    def apply(self, party) -> None:
        """Burst of power followed by increasing HP drain."""
        super().apply(party)

        stacks = party.relics.count(self.id)
        delay = 10 + 2 * (stacks - 1)
        mult = 6.0 + (stacks - 1)
        state = {"mods": {}, "turn": 0}

        def _battle_start(entity) -> None:
            from plugins.foes._base import FoeBase

            if isinstance(entity, FoeBase) or state["mods"]:
                return
            for member in party.members:
                # Emit relic effect event for massive stat boost
                BUS.emit(
                    "relic_effect",
                    "omega_core",
                    member,
                    "stat_amplification",
                    mult,
                    {
                        "multiplier": mult,
                        "duration": "entire_fight",
                        "drain_delay": delay,
                        "stacks": stacks,
                    },
                )

                mod = create_stat_buff(
                    member,
                    name=f"{self.id}_{id(member)}",
                    turns=9999,
                    atk_mult=mult,
                    defense_mult=mult,
                    max_hp_mult=mult,
                    hp_mult=mult,
                    crit_rate_mult=mult,
                    crit_damage_mult=mult,
                    effect_hit_rate_mult=mult,
                    effect_resistance_mult=mult,
                    vitality_mult=mult,
                    mitigation_mult=mult,
                )
                member.effect_manager.add_modifier(mod)
                safe_async_task(member.apply_healing(member.max_hp))
                state["mods"][id(member)] = mod
            state["turn"] = 0

        def _turn_start() -> None:
            if not state["mods"]:
                return
            state["turn"] += 1
            if state["turn"] <= delay:
                return
            drain = (state["turn"] - delay) * 0.01
            for member in party.members:
                dmg = int(member.max_hp * drain)

                # Emit relic effect event for HP drain
                BUS.emit(
                    "relic_effect",
                    "omega_core",
                    member,
                    "hp_drain",
                    dmg,
                    {
                        "drain_percentage": drain * 100,
                        "turn": state["turn"],
                        "turns_past_delay": state["turn"] - delay,
                        "delay": delay,
                    },
                )

                safe_async_task(member.apply_damage(dmg))

        def _battle_end(entity) -> None:
            from plugins.foes._base import FoeBase

            if not isinstance(entity, FoeBase):
                return
            for member in party.members:
                mod = state["mods"].pop(id(member), None)
                if mod:
                    mod.remove()
            state["mods"].clear()

        BUS.subscribe("battle_start", _battle_start)
        BUS.subscribe("turn_start", _turn_start)
        BUS.subscribe("battle_end", _battle_end)

    def describe(self, stacks: int) -> str:
        delay = 10 + 2 * (stacks - 1)
        mult = 6 + (stacks - 1)
        return (
            f"Boosts all ally stats by {mult}x for the entire fight. "
            f"After {delay} turns, allies lose an extra 1% of Max HP each turn."
        )
