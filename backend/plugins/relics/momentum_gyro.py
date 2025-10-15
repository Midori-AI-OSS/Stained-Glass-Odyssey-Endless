from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
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
    about: str = (
        "Repeatedly striking the same foe builds momentum stacks (max 5). "
        "Grants +5% ATK per stack; target loses 5% mitigation per stack for 1 turn. "
        "Resets on target switch or miss."
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

        async def _on_damage_dealt(
            attacker, target, damage, damage_type, source, source_action, action_name, details=None
        ):
            """Track consecutive hits on the same target and apply momentum bonuses."""
            # Check if attacker is a party member
            if attacker not in party.members:
                return

            # Ignore zero damage
            if damage <= 0:
                return

            attacker_id = id(attacker)
            target_id = id(target)
            current_state = getattr(party, "_momentum_gyro_state", state)
            current_stacks = current_state.get("stacks", 0)

            if current_stacks <= 0:
                return

            # Get or initialize chain data for this attacker
            if attacker_id not in chains:
                chains[attacker_id] = {"target": target, "streak": 0}

            chain_data = chains[attacker_id]
            last_target_id = id(chain_data.get("target")) if chain_data.get("target") else None

            # Check if we're hitting the same target
            if last_target_id != target_id:
                # Target changed, reset streak
                chain_data["target"] = target
                chain_data["streak"] = 1
            else:
                # Same target, increment streak (cap at 5)
                chain_data["streak"] = min(chain_data["streak"] + 1, 5)

            streak = chain_data["streak"]

            # Calculate bonuses
            # ATK buff: +5% per streak level per relic stack
            atk_bonus = 0.05 * current_stacks * streak
            # Mitigation debuff: -5% per streak level per relic stack
            mit_debuff = 0.05 * current_stacks * streak

            # Apply ATK buff to attacker
            attacker_mgr = getattr(attacker, "effect_manager", None)
            if attacker_mgr is None:
                attacker_mgr = EffectManager(attacker)
                attacker.effect_manager = attacker_mgr

            # Create temporary ATK buff (1 turn)
            atk_mod = create_stat_buff(
                attacker,
                name=f"{self.id}_momentum_atk",
                turns=1,
                atk_mult=1 + atk_bonus,
            )
            await attacker_mgr.add_modifier(atk_mod)

            log.debug(
                "Momentum Gyro: %s gained +%.1f%% ATK (streak %d, %d relic stacks)",
                getattr(attacker, "id", "member"),
                atk_bonus * 100,
                streak,
                current_stacks,
            )

            # Emit telemetry for attacker buff
            await BUS.emit_async(
                "relic_effect",
                self.id,
                attacker,
                "momentum_atk_buff",
                int(atk_bonus * 100),
                {
                    "atk_bonus_percent": atk_bonus * 100,
                    "streak_level": streak,
                    "relic_stacks": current_stacks,
                    "target": getattr(target, "id", "unknown"),
                    "duration": 1,
                },
            )

            # Apply mitigation debuff to target
            target_mgr = getattr(target, "effect_manager", None)
            if target_mgr is None:
                target_mgr = EffectManager(target)
                target.effect_manager = target_mgr

            # Create mitigation debuff (1 turn)
            # Note: We use atk_mult as a placeholder since mitigation_mult should reduce mitigation
            # The actual stat is mitigation, so 1 - mit_debuff gives the multiplier
            mit_mod = create_stat_buff(
                target,
                name=f"{self.id}_momentum_debuff",
                turns=1,
                mitigation_mult=1 - mit_debuff,
            )
            await target_mgr.add_modifier(mit_mod)

            log.debug(
                "Momentum Gyro: %s received -%.1f%% mitigation (streak %d, %d relic stacks)",
                getattr(target, "id", "foe"),
                mit_debuff * 100,
                streak,
                current_stacks,
            )

            # Emit telemetry for target debuff
            await BUS.emit_async(
                "relic_effect",
                self.id,
                target,
                "momentum_mitigation_debuff",
                int(mit_debuff * 100),
                {
                    "mitigation_reduction_percent": mit_debuff * 100,
                    "streak_level": streak,
                    "relic_stacks": current_stacks,
                    "attacker": getattr(attacker, "id", "unknown"),
                    "duration": 1,
                },
            )

        def _cleanup(*_args) -> None:
            """Clean up subscriptions and state at battle end."""
            self.clear_subscriptions(party)
            chains.clear()
            if getattr(party, "_momentum_gyro_state", None) is state:
                delattr(party, "_momentum_gyro_state")

        self.subscribe(party, "damage_dealt", _on_damage_dealt)
        self.subscribe(party, "battle_end", _cleanup)

    def describe(self, stacks: int) -> str:
        if stacks == 1:
            return (
                "Repeatedly striking the same foe builds momentum stacks (max 5). "
                "Grants +5% ATK per stack; target loses 5% mitigation per stack for 1 turn. "
                "Resets on target switch."
            )
        else:
            atk_per_stack = 5 * stacks
            mit_per_stack = 5 * stacks
            return (
                f"Repeatedly striking the same foe builds momentum stacks (max 5, {stacks} relic stacks). "
                f"Grants +{atk_per_stack}% ATK per momentum stack; "
                f"target loses {mit_per_stack}% mitigation per momentum stack for 1 turn. "
                "Resets on target switch."
            )
