from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task

log = logging.getLogger(__name__)


@dataclass
class EntropyMirror(RelicBase):
    """4★ relic: Amplify enemy ATK at battle start; they suffer recoil when attacking."""

    id: str = "entropy_mirror"
    name: str = "Entropy Mirror"
    stars: int = 4
    effects: dict[str, float] = field(default_factory=dict)
    full_about: str = (
        "A high-risk, high-reward 4-star relic. At battle start, all enemies gain +30% ATK per stack, "
        "making them significantly more dangerous. However, whenever enemies deal damage to party members, "
        "they suffer recoil damage equal to 10% of the damage dealt per stack, applied as cost damage "
        "(bypasses mitigation and shields). Multiple stacks amplify both the ATK buff and recoil "
        "(e.g., 2 stacks = +60% ATK and 20% recoil)."
    )
    summarized_about: str = (
        "Enemies gain atk but suffer recoil when dealing damage"
    )

    async def apply(self, party) -> None:
        await super().apply(party)

        stacks = party.relics.count(self.id)

        # Track state
        state = getattr(party, "_entropy_mirror_state", None)
        if state is None:
            state = {
                "stacks": stacks,
                "buffed_foes": set(),  # Track which foes we've buffed
            }
            party._entropy_mirror_state = state
        else:
            state["stacks"] = stacks

        async def _battle_start(entity) -> None:
            """Buff all foes' ATK at battle start."""
            from plugins.characters.foe_base import FoeBase

            # Check if this is a foe
            if not isinstance(entity, FoeBase):
                return

            current_state = getattr(party, "_entropy_mirror_state", state)
            current_stacks = current_state.get("stacks", 0)

            if current_stacks <= 0:
                return

            # Apply ATK buff (30% per relic stack)
            atk_buff = 0.30 * current_stacks

            mgr = getattr(entity, "effect_manager", None)
            if mgr is None:
                mgr = EffectManager(entity)
                entity.effect_manager = mgr

            # Create ATK buff (permanent for this battle)
            mod = create_stat_buff(
                entity,
                name=f"{self.id}_atk_buff",
                turns=9999,
                atk_mult=1 + atk_buff,
            )
            await mgr.add_modifier(mod)

            # Track that we've buffed this foe
            foe_id = id(entity)
            current_state["buffed_foes"].add(foe_id)

            log.debug(
                "Entropy Mirror: %s received +%.1f%% ATK",
                getattr(entity, "id", "foe"),
                atk_buff * 100,
            )

            # Emit telemetry
            await BUS.emit_async(
                "relic_effect",
                self.id,
                entity,
                "enemy_atk_buff",
                int(atk_buff * 100),
                {
                    "atk_buff_percent": atk_buff * 100,
                    "relic_stacks": current_stacks,
                    "foe": getattr(entity, "id", "unknown"),
                },
            )

        async def _on_damage_dealt(
            attacker, target, damage, damage_type, source, source_action, action_name, details=None
        ):
            """Apply recoil when foes deal damage."""
            from plugins.characters.foe_base import FoeBase

            # Check if attacker is a foe
            if not isinstance(attacker, FoeBase):
                return

            # Check if target is a party member
            if target not in party.members:
                return

            # Only trigger on positive damage
            if damage <= 0:
                return

            # Check if attacker is still alive
            attacker_hp = getattr(attacker, "hp", 0)
            if attacker_hp is None or attacker_hp <= 0:
                return

            current_state = getattr(party, "_entropy_mirror_state", state)
            current_stacks = current_state.get("stacks", 0)

            if current_stacks <= 0:
                return

            # Calculate recoil (10% of damage dealt per stack)
            recoil_pct = 0.10 * current_stacks
            recoil_damage = max(1, int(damage * recoil_pct))

            # Apply recoil as cost damage (ignores mitigation and shields)
            safe_async_task(attacker.apply_cost_damage(recoil_damage))

            log.debug(
                "Entropy Mirror: %s suffered %d recoil damage (%.1f%% of %d)",
                getattr(attacker, "id", "foe"),
                recoil_damage,
                recoil_pct * 100,
                damage,
            )

            # Emit telemetry
            await BUS.emit_async(
                "relic_effect",
                self.id,
                attacker,
                "recoil_damage",
                recoil_damage,
                {
                    "recoil_percentage": recoil_pct * 100,
                    "original_damage": damage,
                    "relic_stacks": current_stacks,
                    "foe": getattr(attacker, "id", "unknown"),
                },
            )

        def _cleanup(*_args) -> None:
            """Clean up subscriptions and state at battle end."""
            self.clear_subscriptions(party)
            current_state = getattr(party, "_entropy_mirror_state", None)
            if current_state is state:
                # Reset state for next battle
                state["buffed_foes"].clear()

        self.subscribe(party, "battle_start", _battle_start)
        self.subscribe(party, "damage_dealt", _on_damage_dealt)
        self.subscribe(party, "battle_end", _cleanup)

    def full_about_stacks(self, stacks: int) -> str:
        """Provide stack-aware description by reusing existing describe logic."""
        return self.describe(stacks)

    def describe(self, stacks: int) -> str:
        atk_buff = 30 * stacks
        recoil_pct = 10 * stacks
        return (
            f"At battle start, all foes gain +{atk_buff}% ATK. "
            f"When foes deal damage, they suffer recoil equal to {recoil_pct}% of damage dealt."
        )
