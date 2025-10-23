from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.effects import EffectManager
from autofighter.stats import BUS
from plugins.cards._base import CardBase
from plugins.hots.radiant_regeneration import RadiantRegeneration

log = logging.getLogger(__name__)


@dataclass
class OraclePrayerCharm(CardBase):
    id: str = "oracle_prayer_charm"
    name: str = "Oracle Prayer Charm"
    stars: int = 1
    effects: dict[str, float] = field(
        default_factory=lambda: {"effect_resistance": 0.03, "vitality": 0.03}
    )
    about: str = "+3% Effect Res & +3% Vitality; First time each ally drops below 45% HP in battle, grant 2-turn Radiant Regeneration HoT"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        # Track which members have received the HoT this battle to enforce once-per-ally limit
        activated_members: set[int] = set()

        async def _check_low_hp() -> None:
            """Check if any party member is below 45% HP and needs Radiant Regeneration."""
            for member in party.members:
                member_id = id(member)

                # Skip if already activated for this member this battle
                if member_id in activated_members:
                    continue

                current_hp = getattr(member, "hp", 0)
                max_hp = getattr(member, "max_hp", 1)

                # Check if member is below 45% HP threshold
                if current_hp / max_hp < 0.45:
                    activated_members.add(member_id)

                    # Get or create effect manager
                    effect_manager = getattr(member, "effect_manager", None)
                    if effect_manager is None:
                        effect_manager = EffectManager(member)
                        member.effect_manager = effect_manager

                    # Create and apply Radiant Regeneration HoT
                    hot = RadiantRegeneration(member, turns=2)
                    await effect_manager.add_hot(hot)

                    log.debug(
                        "Oracle Prayer Charm activated Radiant Regeneration for %s: %d HP/turn for 2 turns",
                        getattr(member, "id", "member"),
                        hot.healing,
                    )

                    # Emit telemetry for the activation
                    await BUS.emit_async(
                        "card_effect",
                        self.id,
                        member,
                        "radiant_regeneration_activation",
                        hot.healing,
                        {
                            "hot_healing_per_turn": hot.healing,
                            "duration": 2,
                            "trigger_threshold": 0.45,
                            "current_hp_ratio": current_hp / max_hp,
                        },
                    )

        async def _on_turn_start(*_) -> None:
            """Check HP at start of each turn."""
            await _check_low_hp()

        async def _on_damage_taken(*_) -> None:
            """Check HP after damage is taken."""
            await _check_low_hp()

        async def _on_battle_end(*_) -> None:
            """Reset activation tracking for next battle."""
            activated_members.clear()

        # Subscribe to relevant events
        self.subscribe("turn_start", _on_turn_start)
        self.subscribe("damage_taken", _on_damage_taken)
        self.subscribe("battle_end", _on_battle_end)
