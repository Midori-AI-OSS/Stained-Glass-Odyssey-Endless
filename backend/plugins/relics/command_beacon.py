from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase

log = logging.getLogger(__name__)


@dataclass
class CommandBeacon(RelicBase):
    """3★ relic: At turn start, fastest ally sacrifices HP so others gain SPD boost."""

    id: str = "command_beacon"
    name: str = "Command Beacon"
    stars: int = 3
    effects: dict[str, float] = field(default_factory=dict)  # No baseline bonus
    about: str = (
        "At turn start, the fastest ally takes 3% Max HP damage (per stack). "
        "All other allies gain +15% SPD for that turn (per stack)."
    )

    async def apply(self, party) -> None:
        await super().apply(party)

        # Track active SPD buffs to remove them at turn end
        active_buffs: dict[int, tuple[object, object]] = {}

        async def _on_turn_start(entity) -> None:
            """Apply SPD boost to all allies except the fastest, who takes HP cost."""
            # Only trigger when an ally starts their turn, not when enemies do
            if entity not in party.members:
                return

            stacks = party.relics.count(self.id)
            if stacks <= 0 or not party.members:
                return

            # Find the fastest ally (highest SPD)
            fastest_ally = None
            highest_spd = -1

            for member in party.members:
                if member.hp <= 0:
                    # Skip dead allies
                    continue

                member_spd = member.spd
                if member_spd > highest_spd:
                    highest_spd = member_spd
                    fastest_ally = member

            if fastest_ally is None:
                return

            # Calculate buffs and costs
            spd_bonus = 0.15 * stacks  # +15% per stack
            hp_cost_pct = 0.03 * stacks  # 3% per stack

            # Apply HP cost to fastest ally
            hp_cost = int(fastest_ally.max_hp * hp_cost_pct)
            if hp_cost > 0:
                # Use apply_cost_damage to prevent shields from blocking it
                await fastest_ally.apply_cost_damage(hp_cost)

                log.debug(
                    "Command Beacon: %s (fastest ally) paid %d HP (%d%% Max HP)",
                    getattr(fastest_ally, "id", "unknown"),
                    hp_cost,
                    int(hp_cost_pct * 100),
                )

                await BUS.emit_async(
                    "relic_effect",
                    self.id,
                    fastest_ally,
                    "coordination_cost",
                    hp_cost,
                    {
                        "ally": getattr(fastest_ally, "id", "unknown"),
                        "hp_cost": hp_cost,
                        "hp_cost_pct": hp_cost_pct * 100,
                        "spd": highest_spd,
                        "stacks": stacks,
                    },
                )

            # Apply SPD buff to all other allies
            buffed_count = 0
            for member in party.members:
                if member is fastest_ally or member.hp <= 0:
                    continue

                # Get or create effect manager
                mgr = getattr(member, "effect_manager", None)
                if mgr is None:
                    mgr = EffectManager(member)
                    member.effect_manager = mgr

                # Create SPD buff for 1 turn
                mod = create_stat_buff(
                    member,
                    name=f"{self.id}_spd_{id(member)}",
                    turns=1,
                    spd_mult=1 + spd_bonus,
                )
                await mgr.add_modifier(mod)

                # Track buff for cleanup
                member_id = id(member)
                active_buffs[member_id] = (member, mod)
                buffed_count += 1

                log.debug(
                    "Command Beacon: %s gained +%d%% SPD (from %s)",
                    getattr(member, "id", "unknown"),
                    int(spd_bonus * 100),
                    getattr(fastest_ally, "id", "unknown"),
                )

            if buffed_count > 0:
                await BUS.emit_async(
                    "relic_effect",
                    self.id,
                    fastest_ally,
                    "speed_coordination",
                    buffed_count,
                    {
                        "coordinator": getattr(fastest_ally, "id", "unknown"),
                        "allies_buffed": buffed_count,
                        "spd_bonus_pct": spd_bonus * 100,
                        "stacks": stacks,
                    },
                )

        def _on_turn_end(*_args) -> None:
            """Remove SPD buffs at turn end."""
            for member_id, (member, mod) in list(active_buffs.items()):
                try:
                    mod.remove()
                    # Clean up from effect manager if still there
                    mgr = getattr(member, "effect_manager", None)
                    if mgr and mod in getattr(mgr, "mods", []):
                        mgr.mods.remove(mod)
                    # Clean up from member's mods list if present
                    if hasattr(member, "mods") and mod.id in member.mods:
                        member.mods.remove(mod.id)
                except Exception as e:
                    log.debug("Command Beacon: Error removing SPD buff: %s", e)

            active_buffs.clear()

        def _on_battle_end(*_args) -> None:
            """Clean up subscriptions and buffs at battle end."""
            _on_turn_end()
            self.clear_subscriptions(party)

        self.subscribe(party, "turn_start", _on_turn_start)
        self.subscribe(party, "turn_end", _on_turn_end)
        self.subscribe(party, "battle_end", _on_battle_end)

    def describe(self, stacks: int) -> str:
        spd_bonus = 15 * stacks
        hp_cost = 3 * stacks
        if stacks == 1:
            return (
                "At turn start, the fastest ally takes 3% Max HP damage. "
                "All other allies gain +15% SPD for that turn."
            )
        else:
            return (
                f"At turn start, the fastest ally takes {hp_cost}% Max HP damage ({stacks} stacks). "
                f"All other allies gain +{spd_bonus}% SPD for that turn."
            )
