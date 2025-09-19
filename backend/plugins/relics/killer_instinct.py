from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.players._base import PlayerBase
from plugins.relics._base import RelicBase


@dataclass
class KillerInstinct(RelicBase):
    """Ultimates grant +75% ATK for the turn; kills grant +50% SPD for two turns."""

    id: str = "killer_instinct"
    name: str = "Killer Instinct"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "Ultimates grant +75% ATK for the turn; kills grant +50% SPD for two turns."

    async def apply(self, party) -> None:
        await super().apply(party)

        stacks = party.relics.count(self.id)
        state = getattr(party, "_killer_instinct_state", None)

        if state is None:
            ultimate_buffs: dict[int, tuple[PlayerBase, object]] = {}
            speed_buffs: dict[int, tuple[PlayerBase, object]] = {}

            def _remove_buff(store: dict[int, tuple[PlayerBase, object]], member_id: int) -> None:
                member_entry = store.pop(member_id, None)
                if member_entry is None:
                    return
                member, mod = member_entry
                mod.remove()
                if mod in member.effect_manager.mods:
                    member.effect_manager.mods.remove(mod)
                if mod.id in member.mods:
                    member.mods.remove(mod.id)

            def _clear_ultimate_buffs() -> None:
                for member_id in list(ultimate_buffs.keys()):
                    _remove_buff(ultimate_buffs, member_id)

            def _clear_speed_buffs() -> None:
                for member_id in list(speed_buffs.keys()):
                    _remove_buff(speed_buffs, member_id)

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
                _remove_buff(ultimate_buffs, id(user))
                ultimate_buffs[id(user)] = (user, mod)

            async def _damage(target, attacker, amount, *_: object) -> None:
                if attacker is None:
                    return
                if target.hp <= 0 and id(attacker) in ultimate_buffs:
                    current_stacks = state.get("stacks", 0)
                    if current_stacks <= 0:
                        return

                    speed_pct = 50 * current_stacks
                    speed_mult = 1 + (0.5 * current_stacks)

                    await BUS.emit_async(
                        "relic_effect",
                        "killer_instinct",
                        attacker,
                        "kill_speed_boost",
                        speed_pct,
                        {
                            "spd_percentage": speed_pct,
                            "trigger": "kill",
                            "duration": "2_turns",
                            "stacks": current_stacks,
                            "killer_damage": amount,
                            "victim": getattr(target, "id", str(target)),
                            "speed_multiplier": speed_mult,
                        },
                    )

                    _remove_buff(speed_buffs, id(attacker))
                    mod = create_stat_buff(
                        attacker,
                        name=f"{self.id}_spd",
                        spd_mult=speed_mult,
                        turns=2,
                    )
                    attacker.effect_manager.add_modifier(mod)
                    speed_buffs[id(attacker)] = (attacker, mod)

            def _turn_end(*_args) -> None:
                _clear_ultimate_buffs()
                # Drop any expired speed buffs that have already been removed by the effect manager
                for member_id, (member, mod) in list(speed_buffs.items()):
                    if mod not in member.effect_manager.mods:
                        speed_buffs.pop(member_id, None)

            def _cleanup(*_args) -> None:
                BUS.unsubscribe("ultimate_used", state["ultimate_handler"])
                BUS.unsubscribe("damage_taken", state["damage_handler"])
                BUS.unsubscribe("turn_end", state["turn_end_handler"])
                BUS.unsubscribe("battle_end", state["cleanup_handler"])
                _clear_ultimate_buffs()
                _clear_speed_buffs()
                if getattr(party, "_killer_instinct_state", None) is state:
                    delattr(party, "_killer_instinct_state")

            state = {
                "stacks": stacks,
                "buffs": ultimate_buffs,
                "speed_buffs": speed_buffs,
                "ultimate_handler": _ultimate,
                "damage_handler": _damage,
                "turn_end_handler": _turn_end,
                "cleanup_handler": _cleanup,
                "clear_buffs": _clear_ultimate_buffs,
                "clear_speed_buffs": _clear_speed_buffs,
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
        spd_pct = 50 * stacks
        return (
            f"Ultimates grant +{pct}% ATK for the turn; kills grant +{spd_pct}% SPD for two turns."
        )
