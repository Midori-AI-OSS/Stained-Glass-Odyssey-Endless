from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
import math
from typing import Any

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase
from plugins.characters.foe_base import FoeBase
from plugins.damage_types.light import Light


@dataclass
class EquilibriumPrism(CardBase):
    """Five-star balance card focused on HP averaging and burst utility."""

    id: str = "equilibrium_prism"
    name: str = "Equilibrium Prism"
    stars: int = 5
    effects: dict[str, float] = field(
        default_factory=lambda: {"atk": 15.0, "defense": 15.0}
    )
    full_about: str = (
        "+1500% ATK & +1500% DEF; at turn start, heal allies toward the party's HP "
        "average without harming them. Each healed ally grants a Balance token; at "
        "5 tokens, grant allies +50% Crit Rate & +50% Mitigation for 1 turn and deal "
        "200% Light damage to the highest-HP foe."
    )
    summarized_about: str = (
        "Boosts atk and def; balances party HP each turn, builds tokens to trigger "
        "burst buffs and damage"
    )

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        registry: dict[str, dict[str, Any]] = getattr(
            party, "_equilibrium_prism_state", {}
        )
        if not registry:
            registry = {}
            party._equilibrium_prism_state = registry

        if registry.get(self.id):
            return

        state: dict[str, Any] = {
            "tokens": 0,
            "foes": [],
        }
        handlers: dict[str, Any] = {}
        registry[self.id] = {"state": state, "handlers": handlers}

        def _cleanup() -> None:
            registry.pop(self.id, None)
            self.cleanup_subscriptions()
            state["foes"].clear()
            state["tokens"] = 0

        def _battle_start(entity) -> None:
            if isinstance(entity, FoeBase) and entity not in state["foes"]:
                state["foes"].append(entity)

        def _battle_end(entity) -> None:
            if isinstance(entity, FoeBase):
                if entity in state["foes"]:
                    state["foes"].remove(entity)
                return

            members = getattr(party, "members", ())
            if entity is None or entity in members or entity is party:
                _cleanup()

        async def _turn_start(*_args) -> None:
            members = [
                member
                for member in getattr(party, "members", ())
                if getattr(member, "max_hp", 0) > 0
            ]
            if not members:
                return

            total_pct = 0.0
            count = 0
            for member in members:
                max_hp = getattr(member, "max_hp", 0)
                if max_hp <= 0:
                    continue
                total_pct += getattr(member, "hp", 0) / max_hp
                count += 1

            if count == 0:
                return

            average_pct = total_pct / count
            healed: list[tuple[Any, int]] = []

            for member in members:
                max_hp = getattr(member, "max_hp", 0)
                if max_hp <= 0:
                    continue
                current_hp = getattr(member, "hp", 0)
                desired_hp = min(
                    max_hp,
                    max(current_hp, math.ceil(average_pct * max_hp)),
                )
                heal_amount = desired_hp - current_hp
                if heal_amount <= 0:
                    continue

                await member.apply_healing(
                    heal_amount,
                    healer=None,
                    source_type="card",
                    source_name=self.id,
                )
                healed.append((member, heal_amount))
                await BUS.emit_async(
                    "card_effect",
                    self.id,
                    member,
                    "balance_redistribution",
                    heal_amount,
                    {
                        "target_id": getattr(member, "id", "ally"),
                        "heal_amount": heal_amount,
                        "average_percent": average_pct * 100,
                    },
                )

            heal_count = len(healed)
            if heal_count == 0:
                return

            state["tokens"] += heal_count
            await BUS.emit_async(
                "card_effect",
                self.id,
                party,
                "balance_tokens",
                state["tokens"],
                {
                    "gained": heal_count,
                    "healed_allies": [
                        getattr(member, "id", "ally") for member, _ in healed
                    ],
                },
            )

            if state["tokens"] < 5:
                return

            state["tokens"] = 0
            await BUS.emit_async(
                "card_effect",
                self.id,
                party,
                "balance_tokens_reset",
                0,
                {"trigger": "burst"},
            )

            for member in members:
                effect_manager = getattr(member, "effect_manager", None)
                if effect_manager is None:
                    effect_manager = EffectManager(member)
                    member.effect_manager = effect_manager

                crit_mod = create_stat_buff(
                    member,
                    name=f"{self.id}_crit_burst",
                    turns=1,
                    crit_rate=0.5,
                )
                mitigation_mod = create_stat_buff(
                    member,
                    name=f"{self.id}_mitigation_burst",
                    turns=1,
                    mitigation_mult=1.5,
                )
                await effect_manager.add_modifier(crit_mod)
                await effect_manager.add_modifier(mitigation_mod)

                await BUS.emit_async(
                    "card_effect",
                    self.id,
                    member,
                    "balance_burst_buff",
                    50,
                    {
                        "crit_bonus": 50,
                        "mitigation_bonus": 50,
                        "duration": 1,
                    },
                )

            living = [
                member
                for member in members
                if getattr(member, "hp", 0) > 0
            ]
            attacker = None
            if living:
                attacker = max(living, key=lambda ally: getattr(ally, "atk", 0))
            elif members:
                attacker = max(members, key=lambda ally: getattr(ally, "atk", 0))

            target = None
            if state["foes"]:
                active_foes = [foe for foe in state["foes"] if getattr(foe, "hp", 0) > 0]
                if active_foes:
                    target = max(active_foes, key=lambda foe: getattr(foe, "hp", 0))

            if attacker is None or target is None:
                return

            damage_amount = int(getattr(attacker, "atk", 0) * 2.0)
            if damage_amount <= 0:
                return

            original_type = getattr(attacker, "damage_type", None)
            swap_type = not isinstance(original_type, Light)
            if swap_type:
                attacker.damage_type = Light()

            try:
                from autofighter.stats import is_battle_active
                from autofighter.stats import set_battle_active
            except ModuleNotFoundError:
                is_battle_active = None
                set_battle_active = None

            battle_was_active = is_battle_active() if is_battle_active else True
            if not battle_was_active and set_battle_active is not None:
                set_battle_active(True)

            try:
                await target.apply_damage(
                    damage_amount,
                    attacker=attacker,
                    action_name="Equilibrium Prism Burst",
                )
            finally:
                if swap_type:
                    attacker.damage_type = original_type
                if not battle_was_active and set_battle_active is not None:
                    set_battle_active(False)

            await BUS.emit_async(
                "card_effect",
                self.id,
                attacker,
                "balance_burst_damage",
                damage_amount,
                {
                    "target_id": getattr(target, "id", "foe"),
                    "damage_type": "Light",
                },
            )

        def _register(event: str, callback) -> None:
            handlers[event] = callback
            self.subscribe(event, callback)

        _register("battle_start", _battle_start)
        _register("battle_end", _battle_end)
        _register("turn_start", _turn_start)
