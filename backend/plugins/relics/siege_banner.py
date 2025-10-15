from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase

log = logging.getLogger(__name__)


@dataclass
class SiegeBanner(RelicBase):
    """3★ relic: Debuffs enemy DEF at battle start; party gains permanent buffs per kill."""

    id: str = "siege_banner"
    name: str = "Siege Banner"
    stars: int = 3
    effects: dict[str, float] = field(default_factory=dict)  # No baseline bonus
    about: str = (
        "At battle start, all enemies lose 15% DEF for 2 turns. "
        "Each enemy killed grants the party +4% ATK and +4% DEF permanently."
    )

    async def apply(self, party) -> None:
        await super().apply(party)

        stacks = party.relics.count(self.id)

        # Track kills for permanent buffs
        state = getattr(party, "_siege_banner_state", None)
        if state is None:
            state = {
                "stacks": stacks,
                "kills": 0,
            }
            party._siege_banner_state = state
        else:
            state["stacks"] = stacks

        async def _battle_start(entity) -> None:
            """Debuff all enemies at battle start."""
            from plugins.characters.foe_base import FoeBase

            # Check if this is a foe
            if isinstance(entity, FoeBase):
                current_state = getattr(party, "_siege_banner_state", state)
                current_stacks = current_state.get("stacks", 0)

                if current_stacks <= 0:
                    return

                # Apply DEF debuff (15% per relic stack)
                def_debuff = 0.15 * current_stacks

                mgr = getattr(entity, "effect_manager", None)
                if mgr is None:
                    mgr = EffectManager(entity)
                    entity.effect_manager = mgr

                # Create DEF debuff (2 turns)
                mod = create_stat_buff(
                    entity,
                    name=f"{self.id}_def_debuff",
                    turns=2,
                    defense_mult=1 - def_debuff,
                )
                await mgr.add_modifier(mod)

                log.debug(
                    "Siege Banner: %s received -%.1f%% DEF for 2 turns",
                    getattr(entity, "id", "foe"),
                    def_debuff * 100,
                )

                # Emit telemetry
                await BUS.emit_async(
                    "relic_effect",
                    self.id,
                    entity,
                    "opening_defense_debuff",
                    int(def_debuff * 100),
                    {
                        "defense_reduction_percent": def_debuff * 100,
                        "duration_turns": 2,
                        "relic_stacks": current_stacks,
                        "foe": getattr(entity, "id", "unknown"),
                    },
                )

        async def _on_kill(target, attacker, amount, *_: object) -> None:
            """Grant permanent buffs to party when a foe dies."""
            # Check if target is dead
            if target.hp > 0:
                return

            # Check if attacker is from our party
            if attacker is None or attacker not in getattr(party, "members", ()):  # type: ignore[arg-type]
                return

            # Check if target is a foe (not a party member)
            if target in party.members:
                return

            current_state = getattr(party, "_siege_banner_state", state)
            current_stacks = current_state.get("stacks", 0)

            if current_stacks <= 0:
                return

            # Increment kill counter
            current_state["kills"] = current_state.get("kills", 0) + 1
            kills = current_state["kills"]

            # Apply permanent buffs to all party members
            # +4% ATK and +4% DEF per kill
            atk_buff = 0.04
            def_buff = 0.04

            for member in party.members:
                mgr = getattr(member, "effect_manager", None)
                if mgr is None:
                    mgr = EffectManager(member)
                    member.effect_manager = mgr

                # Create permanent buff (9999 turns)
                mod = create_stat_buff(
                    member,
                    name=f"{self.id}_kill_{kills}",
                    turns=9999,
                    atk_mult=1 + atk_buff,
                    defense_mult=1 + def_buff,
                )
                await mgr.add_modifier(mod)

            log.debug(
                "Siege Banner: Party gained +%.1f%% ATK and +%.1f%% DEF (kill #%d)",
                atk_buff * 100,
                def_buff * 100,
                kills,
            )

            # Emit telemetry
            await BUS.emit_async(
                "relic_effect",
                self.id,
                attacker,
                "kill_stack_buff",
                int((atk_buff + def_buff) * 100),
                {
                    "atk_bonus_percent": atk_buff * 100,
                    "def_bonus_percent": def_buff * 100,
                    "kill_count": kills,
                    "relic_stacks": current_stacks,
                    "permanent": True,
                    "killed_foe": getattr(target, "id", "unknown"),
                },
            )

        def _cleanup(*_args) -> None:
            """Clean up subscriptions and state at battle end."""
            self.clear_subscriptions(party)
            if getattr(party, "_siege_banner_state", None) is state:
                state["kills"] = 0  # Reset kill counter but keep stacks
                # Only delete the state if we're sure cleanup should remove it entirely
                # For now, just reset kills to allow multi-battle tracking if needed

        self.subscribe(party, "battle_start", _battle_start)
        self.subscribe(party, "damage_taken", _on_kill)
        self.subscribe(party, "battle_end", _cleanup)

    def describe(self, stacks: int) -> str:
        if stacks == 1:
            return (
                "At battle start, all enemies lose 15% DEF for 2 turns. "
                "Each enemy killed grants the party +4% ATK and +4% DEF permanently."
            )
        else:
            def_debuff = 15 * stacks
            return (
                f"At battle start, all enemies lose {def_debuff}% DEF for 2 turns ({stacks} relic stacks). "
                "Each enemy killed grants the party +4% ATK and +4% DEF permanently."
            )
