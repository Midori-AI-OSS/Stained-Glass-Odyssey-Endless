from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase


@dataclass
class SafeguardPrism(RelicBase):
    """When ally drops below 60% HP, grant shield and mitigation (limited triggers per stack)."""

    id: str = "safeguard_prism"
    name: str = "Safeguard Prism"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "When an ally drops below 60% Max HP, grant shield worth 15% Max HP and +12% mitigation for 1 turn (1 trigger per stack per ally per battle)"

    async def apply(self, party) -> None:
        await super().apply(party)

        state = getattr(party, "_safeguard_prism_state", None)
        stacks = party.relics.count(self.id)

        if state is None:
            state = {
                "stacks": stacks,
                "triggers": {},  # Dict mapping ally id to trigger count
            }
            party._safeguard_prism_state = state
        else:
            state["stacks"] = stacks

        def _battle_start(*_args) -> None:
            """Reset trigger counts at battle start."""
            current_state = getattr(party, "_safeguard_prism_state", {})
            current_state["triggers"] = {}

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

            # Track triggers per ally
            ally_id = id(target)
            triggers = current_state.setdefault("triggers", {})
            trigger_count = triggers.get(ally_id, 0)

            # Check if we still have triggers available (one per stack)
            if trigger_count >= current_stacks:
                return

            # Increment trigger count for this ally
            triggers[ally_id] = trigger_count + 1

            # Calculate shield (15% Max HP per stack)
            shield_amount = int(target.max_hp * 0.15 * current_stacks)

            # Apply shield using proper healing pipeline
            # We need to heal to full HP first, then the shield_amount becomes shields
            target.enable_overheal()
            hp_deficit = target.max_hp - target.hp
            total_heal = hp_deficit + shield_amount
            await target.apply_healing(total_heal)

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
                    "current_hp_percentage": (target.hp / target.max_hp) * 100,
                    "shield_percentage": 15 * current_stacks,
                    "mitigation_bonus_percentage": mitigation_bonus * 100,
                    "trigger_count": trigger_count + 1,
                    "max_triggers": current_stacks,
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
        self.subscribe(party, "battle_end", _cleanup)

    def describe(self, stacks: int) -> str:
        shield_pct = 15 * stacks
        mitigation_pct = 12 * stacks
        return f"When an ally drops below 60% Max HP, grant shield worth {shield_pct}% Max HP and +{mitigation_pct}% mitigation for 1 turn ({stacks} trigger{'s' if stacks != 1 else ''} per ally per battle)."
