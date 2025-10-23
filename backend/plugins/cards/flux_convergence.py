from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase
from plugins.damage_types.dark import Dark

log = logging.getLogger(__name__)


@dataclass
class FluxConvergence(CardBase):
    """3★ card: +255% Effect Hit Rate; Track debuff applications and trigger AoE dark damage at 5 stacks."""

    id: str = "flux_convergence"
    name: str = "Flux Convergence"
    stars: int = 3
    effects: dict[str, float] = field(default_factory=lambda: {"effect_hit_rate": 2.55})
    about: str = (
        "+255% Effect Hit Rate; Each debuff applied increments a Flux counter. "
        "At 5 stacks, deal 120% ATK dark damage to all foes and grant the debuffing ally +20% Effect Resistance for 1 turn."
    )

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        # Track flux counter and foes
        state = {
            "flux_count": 0,
            "foes": [],
            "last_source": {},
        }

        async def _on_battle_start(entity) -> None:
            """Track foes when battle starts."""
            if any(entity is member for member in party.members):
                return

            if not hasattr(entity, "id"):
                setattr(entity, "id", f"foe_{id(entity)}")

            if not any(entity is foe for foe in state["foes"]):
                state["foes"].append(entity)

        async def _on_battle_end(*_args) -> None:
            """Reset state when battle ends."""
            state["flux_count"] = 0
            state["foes"].clear()
            state["last_source"].clear()

        async def _on_effect_applied(effect_name, entity, details=None):
            """Track debuff applications and trigger AoE at 5 stacks."""
            if not details or entity is None:
                return

            if entity in party.members:
                return

            effect_type = details.get("effect_type")
            effect_id = details.get("effect_id")
            if effect_type not in {"dot", "stat_modifier"} or effect_id is None:
                return

            manager = getattr(entity, "effect_manager", None)
            if manager is None:
                return

            # Get the effect pool
            if effect_type == "dot":
                pool = manager.dots
            else:
                pool = manager.mods

            # Find the effect
            effect = next((eff for eff in reversed(pool) if getattr(eff, "id", None) == effect_id), None)
            if effect is None:
                return

            # Check if source is from our party, falling back to recent metadata
            source = getattr(effect, "source", None)

            if source is None and isinstance(details.get("source"), str):
                source = next(
                    (
                        member
                        for member in party.members
                        if getattr(member, "id", None) == details["source"]
                    ),
                    None,
                )

            if source is None:
                candidate_id = details.get("source_id") or details.get("applier_id")
                if candidate_id:
                    source = next(
                        (
                            member
                            for member in party.members
                            if getattr(member, "id", None) == candidate_id
                        ),
                        None,
                    )

            if source is None:
                source = state["last_source"].get(id(entity))

            if source is None and len(party.members) == 1:
                source = party.members[0]

            if not any(source is member for member in party.members):
                return

            if not hasattr(source, "id"):
                setattr(source, "id", f"party_member_{id(source)}")

            # Skip duplicate emissions for the same effect instance
            effect_marker = getattr(effect, "_flux_convergence_processed", False)
            if effect_marker:
                return
            setattr(effect, "_flux_convergence_processed", True)

            state["last_source"][id(entity)] = source

            # For stat_modifier, check if it's a debuff (negative values or reductive multipliers)
            if effect_type == "stat_modifier":
                deltas = details.get("deltas") or {}
                multipliers = details.get("multipliers") or {}
                has_negative_delta = any(value < 0 for value in deltas.values())
                has_reductive_multiplier = any(value < 1 for value in multipliers.values())
                if not (has_negative_delta or has_reductive_multiplier):
                    return

            # Increment flux counter
            state["flux_count"] += 1
            current_flux = state["flux_count"]

            log.debug(
                "Flux Convergence: Debuff applied by %s, flux counter at %d",
                getattr(source, "id", "unknown"),
                current_flux,
            )

            await BUS.emit_async(
                "card_effect",
                self.id,
                source,
                "flux_increment",
                current_flux,
                {
                    "flux_count": current_flux,
                    "debuff_source": getattr(source, "id", "unknown"),
                },
            )

            # Trigger at 5 stacks
            if current_flux >= 5:
                # Reset counter
                state["flux_count"] = 0

                # Calculate dark damage (120% ATK)
                damage_amount = int(source.atk * 1.2)

                # Deal damage to all foes
                foes = [f for f in state["foes"] if f.hp > 0]
                damage_type = Dark()

                original_damage_type = getattr(source, "damage_type", None)
                swap_damage_type = original_damage_type is None or getattr(
                    original_damage_type, "id", ""
                ).lower() != damage_type.id.lower()

                if swap_damage_type:
                    source.damage_type = damage_type

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
                    for foe in foes:
                        await foe.apply_damage(
                            damage_amount,
                            attacker=source,
                            action_name="Flux Convergence Burst",
                        )

                        await BUS.emit_async(
                            "card_effect",
                            self.id,
                            source,
                            "flux_burst_damage",
                            damage_amount,
                            {
                                "damage": damage_amount,
                                "target": getattr(foe, "id", "unknown"),
                                "flux_consumed": 5,
                            },
                        )
                finally:
                    if swap_damage_type:
                        source.damage_type = original_damage_type
                    if not battle_was_active and set_battle_active is not None:
                        set_battle_active(False)

                # Grant +20% Effect Resistance for 1 turn to the debuffing ally
                effect_manager = getattr(source, "effect_manager", None)
                if effect_manager is None:
                    effect_manager = EffectManager(source)
                    source.effect_manager = effect_manager

                resistance_mod = create_stat_buff(
                    source,
                    name=f"{self.id}_resistance",
                    turns=1,
                    effect_resistance_mult=1.20,
                )
                await effect_manager.add_modifier(resistance_mod)

                log.debug(
                    "Flux Convergence: Triggered burst! Dealt %d dark damage to %d foes, granted +20%% Effect Resistance to %s",
                    damage_amount,
                    len(foes),
                    getattr(source, "id", "unknown"),
                )

                await BUS.emit_async(
                    "card_effect",
                    self.id,
                    source,
                    "flux_burst_trigger",
                    damage_amount,
                    {
                        "damage": damage_amount,
                        "foes_hit": len(foes),
                        "resistance_bonus": 20,
                        "debuffer": getattr(source, "id", "unknown"),
                    },
                )

        self.subscribe("battle_start", _on_battle_start)
        self.subscribe("battle_end", _on_battle_end)
        self.subscribe("effect_applied", _on_effect_applied)
