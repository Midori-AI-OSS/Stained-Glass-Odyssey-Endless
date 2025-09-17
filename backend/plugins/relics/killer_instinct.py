from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.players._base import PlayerBase
from plugins.relics._base import RelicBase


@dataclass
class KillerInstinct(RelicBase):
    """Ultimates grant +75% ATK for the turn; kills grant another turn."""

    id: str = "killer_instinct"
    name: str = "Killer Instinct"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "Ultimates grant +75% ATK for the turn; kills grant another turn."

    async def apply(self, party) -> None:
        await super().apply(party)

        stacks = party.relics.count(self.id)
        state = getattr(party, "_killer_instinct_state", None)

        if state is None:
            buffs: dict[int, tuple[PlayerBase, object]] = {}

            def _clear_buffs() -> None:
                for _, (member, mod) in list(buffs.items()):
                    mod.remove()
                    if mod in member.effect_manager.mods:
                        member.effect_manager.mods.remove(mod)
                    if mod.id in member.mods:
                        member.mods.remove(mod.id)
                buffs.clear()

            async def _ultimate(user) -> None:
                current_stacks = state.get("stacks", 0)
                if current_stacks <= 0:
                    return
                atk_pct = 75 * current_stacks
                atk_mult = 1 + (0.75 * current_stacks)

                # Emit relic effect event for ultimate ATK boost
                await BUS.emit_async("relic_effect", "killer_instinct", user, "ultimate_atk_boost", atk_pct, {
                    "atk_percentage": atk_pct,
                    "trigger": "ultimate_used",
                    "duration": "1_turn",
                    "stacks": current_stacks
                })

                mod = create_stat_buff(user, name=f"{self.id}_atk", atk_mult=atk_mult, turns=1)
                user.effect_manager.add_modifier(mod)
                buffs[id(user)] = (user, mod)

            async def _damage(target, attacker, amount) -> None:
                if attacker is None:
                    return
                if target.hp <= 0 and id(attacker) in buffs:
                    # Emit relic effect event for extra turn
                    await BUS.emit_async("relic_effect", "killer_instinct", attacker, "extra_turn_grant", 1, {
                        "trigger": "kill",
                        "victim": getattr(target, 'id', str(target)),
                        "killer_damage": amount
                    })

                    await BUS.emit_async("extra_turn", attacker)

            def _turn_end(*_args) -> None:
                _clear_buffs()

            def _cleanup(*_args) -> None:
                BUS.unsubscribe("ultimate_used", state["ultimate_handler"])
                BUS.unsubscribe("damage_taken", state["damage_handler"])
                BUS.unsubscribe("turn_end", state["turn_end_handler"])
                BUS.unsubscribe("battle_end", state["cleanup_handler"])
                _clear_buffs()
                if getattr(party, "_killer_instinct_state", None) is state:
                    delattr(party, "_killer_instinct_state")

            state = {
                "stacks": stacks,
                "buffs": buffs,
                "ultimate_handler": _ultimate,
                "damage_handler": _damage,
                "turn_end_handler": _turn_end,
                "cleanup_handler": _cleanup,
                "clear_buffs": _clear_buffs,
            }
            party._killer_instinct_state = state

            BUS.subscribe("ultimate_used", _ultimate)
            BUS.subscribe("damage_taken", _damage)
            BUS.subscribe("turn_end", _turn_end)
            BUS.subscribe("battle_end", _cleanup)
        else:
            state["stacks"] = stacks

    def describe(self, stacks: int) -> str:
        pct = 75 * stacks
        return f"Ultimates grant +{pct}% ATK for the turn; kills grant another turn."