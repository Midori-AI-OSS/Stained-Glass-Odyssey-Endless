from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class SafeguardPrism(RelicBase):
    """When ally drops below 60% HP, grant shield and mitigation (limited triggers per stack)."""

    id: str = "safeguard_prism"
    name: str = "Safeguard Prism"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    full_about: str = (
        "When a party member drops below 60% Max HP, they immediately receive a shield worth 15% Max HP "
        "per stack and gain +12% mitigation per stack for 1 turn. The shield is applied as overheal on top "
        "of their current HP. After triggering, each ally has a 5-turn cooldown (+1 turn per 5 stacks) before "
        "they can trigger the effect again. Multiple stacks increase shield/mitigation and slightly extend "
        "the cooldown (e.g., 2 stacks = 30% shield, +24% mitigation, 5-turn cooldown)."
    )
    summarized_about: str = (
        "Grants emergency shield and mitigation when allies drop below a health threshold"
    )

    async def apply(self, party) -> None:
        await super().apply(party)

        state = getattr(party, "_safeguard_prism_state", None)
        stacks = party.relics.count(self.id)

        if state is None:
            state = {
                "stacks": stacks,
                "cooldowns": {},  # Dict mapping ally id to the turn index when the relic can fire again
                "turn": 0,
            }
            party._safeguard_prism_state = state
        else:
            state["stacks"] = stacks
            state.setdefault("cooldowns", {})
            state.setdefault("turn", 0)

        def _cooldown_turns(active_stacks: int) -> int:
            return 5 + max(0, active_stacks // 5)

        def _battle_start(*_args) -> None:
            """Reset trigger counts at battle start."""
            current_state = getattr(party, "_safeguard_prism_state", {})
            current_state["cooldowns"] = {}
            current_state["turn"] = 0

        def _turn_advanced(*_args) -> None:
            current_state = getattr(party, "_safeguard_prism_state", None)
            if not current_state:
                return
            current_turn = current_state.get("turn", 0) + 1
            current_state["turn"] = current_turn
            cooldowns = current_state.get("cooldowns", {})
            expired = [ally_id for ally_id, ready_turn in cooldowns.items() if ready_turn <= current_turn]
            for ally_id in expired:
                cooldowns.pop(ally_id, None)

        async def _on_damage_taken(target, attacker, amount, *_args) -> None:
            """Apply shield and mitigation when ally drops below 60% HP."""
            # Check if target is a party member
            if target is None or target not in getattr(party, "members", ()):  # type: ignore[arg-type]
                return

            current_state = getattr(party, "_safeguard_prism_state", {})
            current_stacks = current_state.get("stacks", 0)
            if current_stacks <= 0:
                return

            # Skip if ally is dead (prevent resurrection)
            if target.hp <= 0:
                return

            # Check if ally is below 60% HP
            if target.hp > target.max_hp * 0.60:
                return

            # Track cooldown per ally
            ally_id = id(target)
            cooldowns = current_state.setdefault("cooldowns", {})
            current_turn = current_state.setdefault("turn", 0)
            ready_turn = cooldowns.get(ally_id)
            if ready_turn is not None and current_turn < ready_turn:
                return

            cooldown_turns = max(0, _cooldown_turns(current_stacks))
            next_available_turn = current_turn + cooldown_turns
            if cooldown_turns > 0:
                cooldowns[ally_id] = next_available_turn
            else:
                cooldowns.pop(ally_id, None)

            # Calculate shield (15% Max HP per stack)
            shield_amount = max(1, int(target.max_hp * 0.15 * current_stacks))

            # Apply shield using proper healing pipeline
            hp_before = max(0, target.hp)
            target.enable_overheal()
            hp_deficit = max(0, target.max_hp - target.hp)
            total_heal = max(1, hp_deficit + shield_amount)
            safe_async_task(target.apply_healing(total_heal))

            # Get or create effect manager
            effect_manager = getattr(target, "effect_manager", None)
            if effect_manager is None:
                effect_manager = EffectManager(target)
                target.effect_manager = effect_manager

            # Grant +12% mitigation per stack for 1 turn
            mitigation_bonus = 0.12 * current_stacks
            mitigation_mod = create_stat_buff(
                target,
                name=f"{self.id}_mitigation",
                turns=1,
                mitigation_mult=1 + mitigation_bonus,
            )
            await effect_manager.add_modifier(mitigation_mod)

            # Emit telemetry
            await BUS.emit_async(
                "relic_effect",
                self.id,
                target,
                "emergency_shield",
                shield_amount,
                {
                    "hp_threshold_percentage": 60,
                    "hp_percentage_before": round((hp_before / target.max_hp) * 100, 2) if target.max_hp else 0,
                    "shield_percentage": 15 * current_stacks,
                    "mitigation_bonus_percentage": mitigation_bonus * 100,
                    "cooldown_turns": cooldown_turns,
                    "turn_index": current_turn,
                    "next_available_turn": next_available_turn,
                    "turns_remaining": max(0, next_available_turn - current_turn),
                    "stacks": current_stacks,
                },
            )

        def _cleanup(*_args) -> None:
            """Clean up subscriptions at battle end."""
            self.clear_subscriptions(party)
            if getattr(party, "_safeguard_prism_state", None) is state:
                delattr(party, "_safeguard_prism_state")

        self.subscribe(party, "battle_start", _battle_start)
        self.subscribe(party, "damage_taken", _on_damage_taken)
        self.subscribe(party, "turn_start", _turn_advanced)
        self.subscribe(party, "battle_end", _cleanup)

    def full_about_stacks(self, stacks: int) -> str:
        """Provide stack-aware description by reusing existing describe logic."""
        return self.describe(stacks)

    def describe(self, stacks: int) -> str:
        shield_pct = 15 * stacks
        mitigation_pct = 12 * stacks
        cooldown_turns = 5 + max(0, stacks // 5)
        cooldown_text = "turns" if cooldown_turns != 1 else "turn"
        return (
            "When an ally drops below 60% Max HP, grant a shield worth "
            f"{shield_pct}% Max HP and +{mitigation_pct}% mitigation for 1 turn. "
            f"Each ally must wait {cooldown_turns} {cooldown_text} before the effect can trigger again."
        )
