from dataclasses import dataclass, field
import logging

from autofighter.effects import EffectManager, create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase

log = logging.getLogger(__name__)


@dataclass
class MomentumGyro(RelicBase):
    """2★ relic: Rewards focused assault chains with stacking buffs and enemy debuffs."""

    id: str = "momentum_gyro"
    name: str = "Momentum Gyro"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=dict)  # No baseline bonus
    full_about: str = (
        "Repeatedly striking the same foe builds momentum stacks (max 5). "
        "Grants +5% ATK per stack (extra relic copies beyond five grant +15% each) and "
        "target loses the same mitigation for 5 turns (plus 1 turn per relic stack). "
        "Resets on target switch or miss."
    )
    summarized_about: str = (
        "Rewards focused assault on same target with stacking buffs and enemy debuffs; "
        "resets on target switch"
    )

    async def apply(self, party) -> None:
        await super().apply(party)

        stacks = party.relics.count(self.id)

        # Track momentum chains per attacker: {attacker_id: {"target": target_id, "streak": int}}
        state = getattr(party, "_momentum_gyro_state", None)
        if state is None:
            state = {
                "stacks": stacks,
                "chains": {},  # {attacker_id: {"target": target_obj, "streak": int}}
            }
            party._momentum_gyro_state = state
        else:
            state["stacks"] = stacks

        chains: dict[int, dict] = state.setdefault("chains", {})

        def _remove_modifier(owner, modifier) -> None:
            if modifier is None or owner is None:
                return

            try:
                modifier.remove()
            except Exception:  # pragma: no cover - defensive safeguard
                log.exception("Failed removing Momentum Gyro modifier")

            manager = getattr(owner, "effect_manager", None)
            if manager is not None and modifier in manager.mods:
                manager.mods.remove(modifier)

            if getattr(owner, "mods", None) and modifier.id in owner.mods:
                owner.mods.remove(modifier.id)

        def _clear_chain_effects(attacker_obj, chain_entry: dict) -> None:
            if not chain_entry:
                return

            _remove_modifier(attacker_obj, chain_entry.pop("atk_mod", None))
            target_entry = chain_entry.pop("target_mod", None)
            if target_entry:
                target_obj, target_modifier = target_entry
                _remove_modifier(target_obj, target_modifier)

        def _reset_chain(attacker_obj, chain_entry: dict) -> None:
            _clear_chain_effects(attacker_obj, chain_entry)
            chain_entry["streak"] = 0
            chain_entry["target"] = None

        async def _on_damage_dealt(
            attacker, target, damage, damage_type, source, source_action, action_name, details=None
        ):
            """Track consecutive hits on the same target and apply momentum bonuses."""
            # Check if attacker is a party member
            if attacker not in party.members:
                return

            attacker_id = id(attacker)
            target_id = id(target)
            current_state = getattr(party, "_momentum_gyro_state", state)
            current_stacks = current_state.get("stacks", 0)

            if current_stacks <= 0:
                return

            # Reset streak on zero damage (miss)
            if damage <= 0:
                if attacker_id in chains:
                    _reset_chain(attacker, chains[attacker_id])
                return

            # Get or initialize chain data for this attacker
            if attacker_id not in chains:
                chains[attacker_id] = {"target": None, "streak": 0, "attacker": attacker}

            chain_data = chains[attacker_id]
            chain_data["attacker"] = attacker
            last_target_id = id(chain_data.get("target")) if chain_data.get("target") else None

            # Check if we're hitting the same target
            if last_target_id != target_id:
                # Target changed, reset streak
                if chain_data.get("target") is not None:
                    _reset_chain(attacker, chain_data)
                chain_data["target"] = target
                chain_data["streak"] = 1
            else:
                # Same target, increment streak (cap at 5)
                chain_data["streak"] = min(chain_data["streak"] + 1, 5)

            streak = chain_data["streak"]

            # Calculate bonuses
            base_stacks = min(current_stacks, 5)
            overflow_stacks = max(current_stacks - 5, 0)
            per_hit_multiplier = (base_stacks * 0.05) + (overflow_stacks * 0.15)
            total_multiplier = per_hit_multiplier * streak

            duration_turns = 5 + current_stacks

            # Apply ATK buff to attacker
            attacker_mgr = getattr(attacker, "effect_manager", None)
            if attacker_mgr is None:
                attacker_mgr = EffectManager(attacker)
                attacker.effect_manager = attacker_mgr

            # Create temporary ATK buff whose duration scales with relic copies
            atk_mod = create_stat_buff(
                attacker,
                name=f"{self.id}_momentum_atk",
                turns=duration_turns,
                atk_mult=1 + total_multiplier,
            )
            await attacker_mgr.add_modifier(atk_mod)
            chain_data["atk_mod"] = atk_mod

            log.debug(
                "Momentum Gyro: %s gained +%.1f%% ATK (streak %d, %d relic stacks, %d-turn duration)",
                getattr(attacker, "id", "member"),
                total_multiplier * 100,
                streak,
                current_stacks,
                duration_turns,
            )

            # Emit telemetry for attacker buff
            await BUS.emit_async(
                "relic_effect",
                self.id,
                attacker,
                "momentum_atk_buff",
                int(total_multiplier * 100),
                {
                    "atk_bonus_percent": total_multiplier * 100,
                    "streak_level": streak,
                    "relic_stacks": current_stacks,
                    "base_stack_contribution": base_stacks,
                    "overflow_stack_contribution": overflow_stacks,
                    "target": getattr(target, "id", "unknown"),
                    "duration": duration_turns,
                },
            )

            # Apply mitigation debuff to target
            target_mgr = getattr(target, "effect_manager", None)
            if target_mgr is None:
                target_mgr = EffectManager(target)
                target.effect_manager = target_mgr

            # Create mitigation debuff (duration scales with relic copies)
            # Note: We use atk_mult as a placeholder since mitigation_mult should reduce mitigation
            # The actual stat is mitigation, so 1 - mit_debuff gives the multiplier
            mit_mod = create_stat_buff(
                target,
                name=f"{self.id}_momentum_debuff",
                turns=duration_turns,
                mitigation_mult=1 - total_multiplier,
            )
            await target_mgr.add_modifier(mit_mod)
            chain_data["target_mod"] = (target, mit_mod)

            log.debug(
                "Momentum Gyro: %s received -%.1f%% mitigation (streak %d, %d relic stacks, %d-turn duration)",
                getattr(target, "id", "foe"),
                total_multiplier * 100,
                streak,
                current_stacks,
                duration_turns,
            )

            # Emit telemetry for target debuff
            await BUS.emit_async(
                "relic_effect",
                self.id,
                target,
                "momentum_mitigation_debuff",
                int(total_multiplier * 100),
                {
                    "mitigation_reduction_percent": total_multiplier * 100,
                    "streak_level": streak,
                    "relic_stacks": current_stacks,
                    "base_stack_contribution": base_stacks,
                    "overflow_stack_contribution": overflow_stacks,
                    "attacker": getattr(attacker, "id", "unknown"),
                    "duration": duration_turns,
                },
            )

        def _cleanup(*_args) -> None:
            """Clean up subscriptions and state at battle end."""
            self.clear_subscriptions(party)
            for chain_entry in chains.values():
                attacker_obj = chain_entry.get("attacker")
                _clear_chain_effects(attacker_obj, chain_entry)
            chains.clear()
            if getattr(party, "_momentum_gyro_state", None) is state:
                delattr(party, "_momentum_gyro_state")

        self.subscribe(party, "damage_dealt", _on_damage_dealt)
        self.subscribe(party, "battle_end", _cleanup)

    def full_about_stacks(self, stacks: int) -> str:
        """Provide stack-aware description by reusing existing describe logic."""
        return self.describe(stacks)

    def describe(self, stacks: int) -> str:
        if stacks == 1:
            duration_turns = 5 + stacks
            return (
                "Repeatedly striking the same foe builds momentum stacks (max 5). "
                "Grants +5% ATK per momentum stack; target loses 5% mitigation per momentum stack for "
                f"{duration_turns} turns. "
                "Additional relic copies beyond five boost the per-stack bonus to +15% each. "
                "Resets on target switch."
            )
        else:
            base_stacks = min(stacks, 5)
            overflow_stacks = max(stacks - 5, 0)
            atk_per_stack = (5 * base_stacks) + (15 * overflow_stacks)
            mit_per_stack = atk_per_stack
            duration_turns = 5 + stacks
            return (
                f"Repeatedly striking the same foe builds momentum stacks (max 5, {stacks} relic stacks). "
                f"Grants +{atk_per_stack}% ATK per momentum stack (first five relics give +5% each, extras +15%); "
                f"target loses {mit_per_stack}% mitigation per momentum stack for {duration_turns} turns. "
                "Resets on target switch."
            )
