from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase

log = logging.getLogger(__name__)


@dataclass
class TempestPathfinder(CardBase):
    """2★ card: +55% Dodge; When ally crits, grant +12% Dodge to all allies for 1 turn (once per team turn)."""

    id: str = "tempest_pathfinder"
    name: str = "Tempest Pathfinder"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=lambda: {"dodge_odds": 0.55})
    full_about: str = (
        "+55% Dodge Odds; When an ally crits, grant all allies +12% Dodge for 1 turn "
        "(once per team turn)"
    )
    summarized_about: str = "Boosts dodge odds; allies gain dodge buff when someone crits"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        # Track whether we've triggered the dodge buff this turn
        state = {"triggered_this_turn": False}

        async def _on_damage_taken(
            target,
            attacker,
            damage,
            pre_damage_hp=None,
            post_damage_hp=None,
            is_critical=False,
            *_: object,
        ):
            """Grant party-wide dodge buff when an ally crits."""
            # Check if the attacker is a party member
            if attacker not in party.members:
                return

            # Check if this was a critical hit
            if not is_critical:
                return

            # Check cooldown - only trigger once per team turn
            if state["triggered_this_turn"]:
                return

            state["triggered_this_turn"] = True

            # Grant +12% dodge to all party members for 1 turn
            for member in party.members:
                effect_manager = getattr(member, "effect_manager", None)
                if effect_manager is None:
                    effect_manager = EffectManager(member)
                    member.effect_manager = effect_manager

                dodge_buff = create_stat_buff(
                    member,
                    name=f"{self.id}_crit_dodge",
                    turns=1,
                    dodge_odds_mult=1.12,  # +12% dodge
                )
                await effect_manager.add_modifier(dodge_buff)

            log.debug(
                "Tempest Pathfinder triggered: %s crit, granting party +12%% dodge for 1 turn",
                getattr(attacker, "id", "member"),
            )

            # Emit telemetry for the buff
            await BUS.emit_async(
                "card_effect",
                self.id,
                attacker,
                "crit_dodge_rally",
                12,
                {
                    "dodge_bonus_percent": 12,
                    "duration": 1,
                    "triggering_member": getattr(attacker, "id", "unknown"),
                    "cooldown_active": True,
                },
            )

        async def _on_turn_start(*_) -> None:
            """Reset cooldown at the start of each turn."""
            state["triggered_this_turn"] = False

        async def _on_battle_end(*_) -> None:
            """Clean up state at battle end."""
            state["triggered_this_turn"] = False

        # Subscribe to relevant events
        self.subscribe("damage_taken", _on_damage_taken)
        self.subscribe("turn_start", _on_turn_start)
        self.subscribe("battle_end", _on_battle_end)
