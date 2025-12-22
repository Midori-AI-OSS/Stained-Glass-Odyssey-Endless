from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any, Iterable

from autofighter.stat_effect import StatEffect
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class SupercellConductor(CardBase):
    """Four-star card that injects periodic Tailwind bonus actions."""

    id: str = "supercell_conductor"
    name: str = "Supercell Conductor"
    stars: int = 4
    effects: dict[str, float] = field(
        default_factory=lambda: {"atk": 2.4, "effect_hit_rate": 2.4}
    )
    full_about: str = (
        "+240% ATK & +240% Effect Hit Rate; at battle start and every third round, "
        "the fastest Wind or Lightning ally gains Tailwind: immediately queue a "
        "bonus action at 50% damage with +30% Effect Hit Rate, then shred -10% "
        "Mitigation from foes they strike for 1 turn."
    )
    summarized_about: str = (
        "Greatly boosts atk and effect hit rate; periodically grants fastest wind/lightning ally "
        "bonus action with mitigation shred"
    )

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        registry: dict[str, dict[str, Any]] = getattr(
            party, "_supercell_conductor_state", {}
        )
        if not registry:
            registry = {}
            party._supercell_conductor_state = registry
        if registry.get(self.id):
            return

        state: dict[str, Any] = {
            "round_counter": 0,
            "next_activation": 1,
            "actors_remaining": set(),
            "current": None,
            "battle_started": False,
        }
        handlers: dict[str, Any] = {}
        registry[self.id] = {"state": state, "handlers": handlers}

        def _cleanup() -> None:
            registry.pop(self.id, None)
            current = state.get("current")
            if current is not None:
                _clear_modifier(current)
                state["current"] = None
            state["actors_remaining"].clear()
            state["round_counter"] = 0
            state["next_activation"] = 1
            state["battle_started"] = False
            self.cleanup_subscriptions()

        def _living_members() -> list[Any]:
            return [
                member
                for member in getattr(party, "members", ())
                if getattr(member, "hp", 0) > 0
            ]

        def _eligible_members(members: Iterable[Any]) -> list[Any]:
            eligible: list[Any] = []
            for member in members:
                damage_type = getattr(member, "damage_type", None)
                ident = getattr(damage_type, "id", None)
                if ident is None:
                    continue
                try:
                    lower_ident = str(ident).lower()
                except Exception:
                    continue
                if lower_ident not in {"wind", "lightning"}:
                    continue
                eligible.append(member)
            return eligible

        def _clear_modifier(current: dict[str, Any]) -> None:
            ally = current.get("ally")
            effect_name = current.get("effect_name")
            if ally is None or not effect_name:
                current["active"] = False
                current["foes"] = {}
                return
            with suppress(Exception):
                ally.remove_effect_by_name(effect_name)
            mods = getattr(ally, "mods", None)
            if isinstance(mods, list):
                mods[:] = [mid for mid in mods if mid != effect_name]
            current["effect_name"] = None
            current["active"] = False
            current["foes"] = {}

        async def _apply_mitigation_shred(current: dict[str, Any]) -> None:
            foes: dict[int, Any] = current.get("foes", {})
            ally = current.get("ally")
            if ally is None:
                return
            if not foes:
                return
            for foe in list(foes.values()):
                if getattr(foe, "hp", 0) <= 0:
                    continue
                mitigation_effect = StatEffect(
                    name=f"{self.id}_tailwind_shred",
                    stat_modifiers={"mitigation": -0.1},
                    duration=1,
                    source=self.id,
                )
                foe.add_effect(mitigation_effect)
                await BUS.emit_async(
                    "card_effect",
                    self.id,
                    foe,
                    "tailwind_mitigation_shred",
                    -10,
                    {
                        "target_id": getattr(foe, "id", "foe"),
                        "mitigation_change_percent": -10,
                        "duration": 1,
                        "source": getattr(ally, "id", None),
                    },
                )

        async def _activate_bonus_turn(ally: Any) -> None:
            current = state.get("current")
            if not current or current.get("active"):
                return
            _clear_modifier(current)
            current_atk = getattr(ally, "atk", 0)
            target_atk = int(round(current_atk * 0.5))
            atk_delta = target_atk - current_atk

            current_effect_hit = getattr(ally, "effect_hit_rate", 0.0)
            target_effect_hit = current_effect_hit * 1.3
            effect_delta = target_effect_hit - current_effect_hit

            effect_name = f"{self.id}_tailwind_bonus"
            bonus_effect = StatEffect(
                name=effect_name,
                stat_modifiers={
                    "atk": atk_delta,
                    "effect_hit_rate": effect_delta,
                },
                duration=2,
                source=self.id,
            )
            ally.add_effect(bonus_effect)
            mods = getattr(ally, "mods", None)
            if isinstance(mods, list):
                mods[:] = [mid for mid in mods if mid != effect_name]
                mods.append(effect_name)
            current["effect_name"] = effect_name
            current["active"] = True
            current["foes"] = {}
            await BUS.emit_async(
                "card_effect",
                self.id,
                ally,
                "tailwind_bonus_prepared",
                50,
                {
                    "effect_hit_bonus_percent": 30,
                    "damage_modifier_percent": 50,
                    "ally_id": getattr(ally, "id", "ally"),
                },
            )

        async def _trigger_tailwind() -> None:
            if state.get("current") is not None:
                state["next_activation"] += 3
                return
            members = _living_members()
            candidates = _eligible_members(members)
            if not candidates:
                state["next_activation"] += 3
                return
            ally = max(
                candidates,
                key=lambda member: (
                    getattr(member, "spd", 0),
                    getattr(member, "actions_per_turn", 1),
                    getattr(member, "atk", 0),
                ),
            )
            current = {
                "ally": ally,
                "effect_name": None,
                "foes": {},
                "has_acted": False,
                "active": False,
            }
            state["current"] = current
            state["next_activation"] += 3
            await BUS.emit_async(
                "card_effect",
                self.id,
                ally,
                "tailwind_granted",
                1,
                {
                    "ally_id": getattr(ally, "id", "ally"),
                    "next_round_trigger": state["next_activation"],
                },
            )
            await BUS.emit_async("extra_turn", ally)

        async def _handle_battle_start(entity, *_args) -> None:
            if entity not in getattr(party, "members", ()):  # ignore foe pulses
                return
            if state["battle_started"]:
                return
            state["battle_started"] = True
            state["actors_remaining"].clear()
            state["round_counter"] = 0
            state["next_activation"] = 1
            await _trigger_tailwind()

        async def _handle_battle_end(entity) -> None:
            if entity in getattr(party, "members", ()):
                _cleanup()

        async def _on_turn_start(actor=None, *_args) -> None:
            if actor is None:
                members = _living_members()
            else:
                members = _living_members()
            if not members:
                return
            living_ids = {id(member) for member in members}
            remaining: set[int] = state["actors_remaining"]
            remaining &= living_ids

            current = state.get("current")
            if current is not None and (
                getattr(current.get("ally"), "hp", 0) <= 0 or current.get("ally") not in members
            ):
                _clear_modifier(current)
                state["current"] = None

            if not remaining:
                state["round_counter"] += 1
                remaining.update(living_ids)
                if (
                    state["round_counter"] >= state["next_activation"]
                    and state.get("current") is None
                ):
                    await _trigger_tailwind()

            if actor in members:
                actor_id = id(actor)
                if actor_id in remaining:
                    remaining.remove(actor_id)
                current = state.get("current")
                if current and actor is current.get("ally"):
                    if not current.get("has_acted"):
                        current["has_acted"] = True
                    else:
                        await _activate_bonus_turn(actor)

        async def _on_hit_landed(attacker, target, *_extra) -> None:
            current = state.get("current")
            if not current or not current.get("active"):
                return
            ally = current.get("ally")
            if attacker is not ally:
                return
            if getattr(target, "hp", 0) <= 0:
                return
            foes = current.setdefault("foes", {})
            foes[id(target)] = target

        async def _on_action_used(actor, *_extra) -> None:
            current = state.get("current")
            if not current or actor is not current.get("ally"):
                return
            if not current.get("active"):
                return
            await _apply_mitigation_shred(current)
            ally = current.get("ally")
            await BUS.emit_async(
                "card_effect",
                self.id,
                ally,
                "tailwind_bonus_spent",
                len(current.get("foes", {})),
                {
                    "ally_id": getattr(ally, "id", "ally"),
                    "foes_affected": [
                        getattr(foe, "id", "foe")
                        for foe in current.get("foes", {}).values()
                    ],
                },
            )
            _clear_modifier(current)
            state["current"] = None

        def _register(event: str, callback) -> None:
            handlers[event] = callback
            self.subscribe(event, callback)

        _register("battle_start", _handle_battle_start)
        _register("battle_end", _handle_battle_end)
        _register("turn_start", _on_turn_start)
        _register("hit_landed", _on_hit_landed)
        _register("action_used", _on_action_used)
