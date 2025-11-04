from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
import math
from typing import Optional

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class GuardianChoirCircuit(CardBase):
    id: str = "guardian_choir_circuit"
    name: str = "Guardian Choir Circuit"
    stars: int = 3
    effects: dict[str, float] = field(
        default_factory=lambda: {"defense": 2.0, "regain": 1.5}
    )
    full_about: str = (
        "+200% DEF & +150% Regain; first direct heal each ally turn redirects "
        "15% as a shield to the lowest-HP teammate and grants them +12% "
        "mitigation for 1 turn."
    )
    summarized_about: str = (
        "Boosts def and regain massively; first heal each turn redirects some "
        "healing as shield and mitigation to lowest-HP ally"
    )

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        turn_counters: dict[int, int] = {}
        triggered_turn: dict[int, int] = {}
        active_shields: dict[int, int] = {}
        active_mitigations: dict[int, bool] = {}
        granted_overheal: set[int] = set()

        def _maybe_disable_overheal(target) -> None:
            target_id = id(target)
            if target_id not in granted_overheal:
                return
            if not getattr(target, "overheal_enabled", False):
                granted_overheal.discard(target_id)
                return
            remaining_shields = getattr(target, "shields", 0)
            if not hasattr(target, "disable_overheal"):
                granted_overheal.discard(target_id)
                return
            target.disable_overheal()
            if remaining_shields > 0:
                target.shields = remaining_shields
            granted_overheal.discard(target_id)

        def _reset_state() -> None:
            for member_id, amount in list(active_shields.items()):
                for member in party.members:
                    if id(member) == member_id and getattr(member, "shields", 0) > 0:
                        to_remove = min(member.shields, amount)
                        member.shields = max(0, member.shields - to_remove)
                        _maybe_disable_overheal(member)
                        break
            for member_id in list(active_mitigations):
                for member in party.members:
                    if id(member) == member_id:
                        _remove_mitigation(member)
                        _maybe_disable_overheal(member)
                        break
            for member in party.members:
                _maybe_disable_overheal(member)
            turn_counters.clear()
            triggered_turn.clear()
            active_shields.clear()
            active_mitigations.clear()
            granted_overheal.clear()

        def _resolve_actor(healer, target):
            if healer in party.members:
                return healer
            if target in party.members:
                return target
            return None

        def _lowest_hp_member() -> Optional[object]:
            candidates = [
                member
                for member in party.members
                if getattr(member, "hp", 0) > 0
            ]
            if not candidates:
                return None

            def _ratio(member) -> tuple[float, float]:
                max_hp = getattr(member, "max_hp", 1) or 1
                current_hp = getattr(member, "hp", 0)
                # Compare by HP ratio first, then absolute HP to stabilize ordering
                return (current_hp / max_hp, current_hp)

            return min(candidates, key=_ratio)

        def _remove_mitigation(target) -> None:
            effect_id = f"{self.id}_mitigation"
            mgr = getattr(target, "effect_manager", None)
            if mgr is not None:
                for existing in list(getattr(mgr, "mods", [])):
                    if existing.id == effect_id:
                        existing.remove()
                        try:
                            mgr.mods.remove(existing)
                        except ValueError:
                            pass
                        break
            mods = getattr(target, "mods", None)
            if mods is not None:
                while effect_id in mods:
                    mods.remove(effect_id)
            if hasattr(target, "remove_effect_by_name"):
                try:
                    target.remove_effect_by_name(effect_id)
                except Exception:
                    pass

        async def _on_turn_start(actor=None, *_args) -> None:
            if actor in party.members:
                actor_id = id(actor)
                turn_counters[actor_id] = turn_counters.get(actor_id, 0) + 1
                triggered_turn.pop(actor_id, None)

                pending_shield = active_shields.pop(actor_id, 0)
                if pending_shield > 0 and getattr(actor, "shields", 0) > 0:
                    to_remove = min(actor.shields, pending_shield)
                    actor.shields = max(0, actor.shields - to_remove)
                _maybe_disable_overheal(actor)

                if active_mitigations.pop(actor_id, False):
                    _remove_mitigation(actor)
                    _maybe_disable_overheal(actor)

        async def _on_battle_start(*_args) -> None:
            _reset_state()

        async def _on_battle_end(*_args) -> None:
            _reset_state()

        async def _on_heal_received(target, healer, heal_amount, *_args) -> None:
            if target not in party.members:
                return
            if heal_amount is None or heal_amount <= 0:
                return

            actor = _resolve_actor(healer, target)
            if actor is None:
                return

            actor_id = id(actor)
            current_turn = turn_counters.get(actor_id, 0)
            if triggered_turn.get(actor_id) == current_turn:
                return

            recipient = _lowest_hp_member()
            if recipient is None:
                return

            shield_request = max(0, math.ceil(float(heal_amount) * 0.15))
            if shield_request <= 0:
                return

            triggered_turn[actor_id] = current_turn

            recipient_id = id(recipient)

            if not getattr(recipient, "overheal_enabled", False):
                recipient.enable_overheal()
                granted_overheal.add(recipient_id)

            shield_before = getattr(recipient, "shields", 0)
            if shield_before <= 0:
                shield_applied = shield_request
            else:
                shield_applied = max(1, int(shield_request * 0.2))

            recipient.shields = shield_before + shield_applied
            active_shields[recipient_id] = active_shields.get(recipient_id, 0) + shield_applied

            effect_manager: EffectManager | None = getattr(
                recipient, "effect_manager", None
            )
            if effect_manager is None:
                effect_manager = EffectManager(recipient)
                recipient.effect_manager = effect_manager

            mitigation_bonus = 0.12
            mitigation_effect = create_stat_buff(
                recipient,
                name=f"{self.id}_mitigation",
                turns=1,
                mitigation_mult=1 + mitigation_bonus,
            )
            await effect_manager.add_modifier(mitigation_effect)
            active_mitigations[recipient_id] = True

            await BUS.emit_async(
                "card_effect",
                self.id,
                recipient,
                "guardian_choir_redirect",
                shield_applied,
                {
                    "heal_amount": heal_amount,
                    "shield_request": shield_request,
                    "shield_applied": shield_applied,
                    "recipient_id": getattr(recipient, "id", "unknown"),
                    "healer_id": getattr(actor, "id", "unknown"),
                    "turn": current_turn,
                    "mitigation_bonus_percent": mitigation_bonus * 100,
                    "shield_before": shield_before,
                    "shield_after": getattr(recipient, "shields", 0),
                },
            )

        self.subscribe("battle_start", _on_battle_start)
        self.subscribe("battle_end", _on_battle_end)
        self.subscribe("turn_start", _on_turn_start)
        self.subscribe("heal_received", _on_heal_received)
