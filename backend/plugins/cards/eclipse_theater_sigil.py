from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import Any
from typing import Dict
from typing import List

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.cards._base import CardBase
from plugins.characters.foe_base import FoeBase
from plugins.dots.abyssal_weakness import AbyssalWeakness
from plugins.hots.radiant_regeneration import RadiantRegeneration


@dataclass
class EclipseTheaterSigil(CardBase):
    """Persona Light/Dark rotation card."""

    id: str = "eclipse_theater_sigil"
    name: str = "Eclipse Theater Sigil"
    stars: int = 5
    effects: dict[str, float] = field(
        default_factory=lambda: {"max_hp": 15.0, "atk": 15.0}
    )
    about: str = (
        "+1500% Max HP & ATK. Alternates Light/Dark each turn: Light cleanses one DoT "
        "per ally and grants 2-turn Radiant Regeneration, Dark inflicts Abyssal "
        "Weakness on foes and gives allies a one-action +50% crit burst."
    )

    async def apply(self, party):  # type: ignore[override]
        await super().apply(party)

        state_store: Dict[str, Dict[str, Any]] = getattr(
            party, "_eclipse_theater_state", {}
        )
        if not state_store:
            party._eclipse_theater_state = state_store

        if self.id in state_store:
            return

        state: Dict[str, Any] = {
            "battle_active": False,
            "turn_index": 0,
            "polarity": "Light",
            "foes": [],
            "crit_mods": {},
        }
        state_store[self.id] = state

        async def _reset_state() -> None:
            await _clear_crit_mods()
            state["turn_index"] = 0
            state["polarity"] = "Light"
            state["battle_active"] = False
            foes: List[Stats] = state.get("foes", [])
            foes.clear()

        async def _battle_start(entity: Stats | None, *_args: object) -> None:
            if entity in getattr(party, "members", []):
                state["battle_active"] = True
                state["turn_index"] = 0
                state["polarity"] = "Light"
                await _clear_crit_mods()
                return

            if isinstance(entity, FoeBase):
                foes: List[Stats] = state.get("foes", [])
                if entity not in foes:
                    foes.append(entity)

        async def _battle_end(entity: Stats | None, *_args: object) -> None:
            if entity is None or entity is party or entity in getattr(party, "members", []):
                await _reset_state()
                return

            if isinstance(entity, FoeBase):
                foes: List[Stats] = state.get("foes", [])
                if entity in foes:
                    foes.remove(entity)

        async def _turn_start(actor: Stats | None = None, *_args: object) -> None:
            if not state.get("battle_active"):
                return

            state["turn_index"] = int(state.get("turn_index", 0)) + 1
            turn_index = state["turn_index"]
            polarity = "Light" if turn_index % 2 == 1 else "Dark"
            state["polarity"] = polarity

            if polarity == "Light":
                await _handle_light_turn(actor, turn_index)
            else:
                await _handle_dark_turn(actor, turn_index)

        async def _action_used(actor: Stats | None, *_args: object) -> None:
            if actor not in getattr(party, "members", []):
                return

            entry = state["crit_mods"].pop(id(actor), None)
            if entry is None:
                return

            _remove_crit_entry(entry)
            await BUS.emit_async(
                "card_effect",
                self.id,
                actor,
                "dark_crit_consumed",
                0,
                {
                    "polarity": state.get("polarity"),
                    "turn_index": state.get("turn_index"),
                    "ally_id": getattr(actor, "id", None),
                },
            )

        async def _clear_crit_mods() -> None:
            crit_mods: Dict[int, Dict[str, Any]] = state.get("crit_mods", {})
            for entry in list(crit_mods.values()):
                _remove_crit_entry(entry)
            crit_mods.clear()

        def _remove_crit_entry(entry: Dict[str, Any]) -> None:
            mod = entry.get("modifier")
            member = entry.get("member")
            manager: EffectManager | None = entry.get("manager")
            if mod is None or member is None:
                return
            try:
                mod.remove()
            except Exception:
                pass
            if manager is not None and mod in getattr(manager, "mods", []):
                try:
                    manager.mods.remove(mod)
                except ValueError:
                    pass
            if hasattr(member, "mods"):
                while getattr(mod, "id", None) in getattr(member, "mods", []):
                    try:
                        member.mods.remove(mod.id)
                    except ValueError:
                        break

        async def _handle_light_turn(actor: Stats | None, turn_index: int) -> None:
            await _clear_crit_mods()

            cleansed: List[dict[str, Any]] = []
            hots: List[dict[str, Any]] = []
            for member in list(getattr(party, "members", [])):
                if getattr(member, "hp", 0) <= 0:
                    continue
                manager = getattr(member, "effect_manager", None)
                if manager is None:
                    manager = EffectManager(member)
                    member.effect_manager = manager

                removed = None
                if manager.dots:
                    removed = manager.dots.pop(0)
                    if hasattr(member, "dots"):
                        while removed.id in member.dots:
                            member.dots.remove(removed.id)
                    BUS.emit_batched(
                        "dot_cleansed",
                        actor,
                        member,
                        getattr(removed, "id", None),
                        {
                            "dot_name": getattr(removed, "name", None),
                            "remaining_turns": getattr(removed, "turns", None),
                            "dot_damage": getattr(removed, "damage", None),
                        },
                    )
                    cleansed.append(
                        {
                            "ally_id": getattr(member, "id", None),
                            "dot_id": getattr(removed, "id", None),
                            "dot_name": getattr(removed, "name", None),
                        }
                    )

                await manager.remove_hots(
                    lambda hot: getattr(hot, "id", "") == RadiantRegeneration.id
                )
                regen = RadiantRegeneration(member, turns=2)
                await manager.add_hot(regen)
                hots.append(
                    {
                        "ally_id": getattr(member, "id", None),
                        "healing": getattr(regen, "healing", None),
                    }
                )

            await BUS.emit_async(
                "card_effect",
                self.id,
                actor,
                "light_polarity",
                len(hots),
                {
                    "polarity": "Light",
                    "turn_index": turn_index,
                    "cleansed": cleansed,
                    "hots_applied": hots,
                },
            )

        async def _handle_dark_turn(actor: Stats | None, turn_index: int) -> None:
            foes: List[Stats] = state.get("foes", [])
            alive_foes = [foe for foe in foes if getattr(foe, "hp", 0) > 0]
            dots_applied: List[dict[str, Any]] = []
            crit_targets: List[dict[str, Any]] = []

            highest_atk = max((getattr(member, "atk", 0) for member in getattr(party, "members", [])), default=0)
            dot_damage = max(int(highest_atk * 0.3), 15)

            for foe in alive_foes:
                manager = getattr(foe, "effect_manager", None)
                if manager is None:
                    manager = EffectManager(foe)
                    foe.effect_manager = manager
                dot = AbyssalWeakness(dot_damage, 2)
                await manager.add_dot(dot)
                dots_applied.append(
                    {
                        "foe_id": getattr(foe, "id", None),
                        "damage": dot.damage,
                        "turns": dot.turns,
                    }
                )

            await _clear_crit_mods()
            for member in list(getattr(party, "members", [])):
                if getattr(member, "hp", 0) <= 0:
                    continue
                manager = getattr(member, "effect_manager", None)
                if manager is None:
                    manager = EffectManager(member)
                    member.effect_manager = manager
                modifier = create_stat_buff(
                    member,
                    name=f"{self.id}_crit_{id(member)}",
                    turns=1,
                    crit_rate=0.5,
                )
                await manager.add_modifier(modifier)
                state["crit_mods"][id(member)] = {
                    "modifier": modifier,
                    "member": member,
                    "manager": manager,
                }
                crit_targets.append(
                    {
                        "ally_id": getattr(member, "id", None),
                        "modifier": modifier.id,
                    }
                )

            await BUS.emit_async(
                "card_effect",
                self.id,
                actor,
                "dark_polarity",
                len(dots_applied),
                {
                    "polarity": "Dark",
                    "turn_index": turn_index,
                    "dots_applied": dots_applied,
                    "crit_buffs": crit_targets,
                },
            )

        self.subscribe("battle_start", _battle_start, cleanup_event=None)
        self.subscribe("battle_end", _battle_end, cleanup_event=None)
        self.subscribe("turn_start", _turn_start, cleanup_event=None)
        self.subscribe("action_used", _action_used, cleanup_event=None)
