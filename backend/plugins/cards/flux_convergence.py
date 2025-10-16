from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase
from plugins.cards._base import safe_async_task
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
        }

        async def _on_battle_start(entity) -> None:
            """Track foes when battle starts."""
            from plugins.characters.foe_base import FoeBase

            if isinstance(entity, FoeBase) and entity not in state["foes"]:
                state["foes"].append(entity)

        async def _on_battle_end(*_args) -> None:
            """Reset state when battle ends."""
            state["flux_count"] = 0
            state["foes"].clear()

        async def _on_effect_applied(effect_name, entity, details=None):
            """Track debuff applications and trigger AoE at 5 stacks."""
            if not details or entity is None:
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

            # Check if source is from our party
            source = getattr(effect, "source", None)
            if source not in party.members:
                return

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

                for foe in foes:
                    # Apply damage with dark damage type
                    safe_async_task(
                        foe.apply_damage(
                            damage_amount,
                            attacker=source,
                            damage_type=damage_type,
                            action_name="Flux Convergence Burst",
                        )
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
