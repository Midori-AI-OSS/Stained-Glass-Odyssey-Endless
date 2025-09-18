from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase


@dataclass
class ShinyPebble(RelicBase):
    """Raises DEF and gives a mitigation burst on the first hit."""

    id: str = "shiny_pebble"
    name: str = "Shiny Pebble"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"defense": 0.03})
    about: str = (
        "Boosts DEF and grants extra mitigation the first time an ally is hit."
    )

    async def apply(self, party) -> None:
        await super().apply(party)

        state = getattr(party, "_shiny_pebble_state", None)
        if state is None:
            state = {"active": {}, "triggered": set()}
            party._shiny_pebble_state = state

            async def _first_hit(target, attacker, amount, *_: object) -> None:
                if target not in party.members or id(target) in state["triggered"]:
                    return
                state["triggered"].add(id(target))
                stacks = party.relics.count(self.id)
                mit_mult = 1 + 0.03 * stacks
                mod = create_stat_buff(
                    target,
                    name=f"{self.id}_{id(target)}",
                    mitigation=target.mitigation * (mit_mult - 1),
                    turns=1,
                )
                target.effect_manager.add_modifier(mod)
                state["active"][id(target)] = (target, mod)

                # Track mitigation burst application
                await BUS.emit_async(
                    "relic_effect",
                    "shiny_pebble",
                    target,
                    "mitigation_burst",
                    int((mit_mult - 1) * 100),
                    {
                        "target": getattr(target, 'id', str(target)),
                        "mitigation_multiplier": mit_mult,
                        "base_mitigation": target.mitigation,
                        "duration_turns": 1,
                        "trigger": "first_hit",
                        "stacks": stacks,
                    },
                )

            def _reset(*_) -> None:
                for key, (member, mod) in list(state["active"].items()):
                    mod.remove()
                    if mod in member.effect_manager.mods:
                        member.effect_manager.mods.remove(mod)
                    if mod.id in member.mods:
                        member.mods.remove(mod.id)
                    state["active"].pop(key, None)

            BUS.subscribe("damage_taken", _first_hit)
            BUS.subscribe("turn_start", _reset)

    def describe(self, stacks: int) -> str:
        if stacks == 1:
            return (
                "+3% DEF. The first time each ally is hit, they gain +3% mitigation for one turn."
            )
        else:
            # Defense stacks multiplicatively; mitigation adds linearly per stack
            total_def_mult = (1.03 ** stacks - 1) * 100
            mit = 3 * stacks  # +3% mitigation for each stack
            return (
                f"+{total_def_mult:.1f}% DEF ({stacks} stacks, multiplicative). "
                f"The first time each ally is hit, they gain +{mit}% mitigation for one turn."
            )