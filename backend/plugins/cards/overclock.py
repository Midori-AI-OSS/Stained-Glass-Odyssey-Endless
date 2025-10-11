import asyncio
from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from autofighter.stats import GAUGE_START
from autofighter.stats import Stats
from plugins.cards._base import CardBase
from plugins.cards._base import safe_async_task


@dataclass
class Overclock(CardBase):
    """+500% ATK & Effect Hit Rate; allies surge with speed at battle start."""

    id: str = "overclock"
    name: str = "Overclock"
    stars: int = 4
    effects: dict[str, float] = field(
        default_factory=lambda: {"atk": 5, "effect_hit_rate": 5}
    )
    about: str = (
        "+500% ATK & +500% Effect Hit Rate; at the start of each battle, "
        "all allies gain +200% SPD for 2 turns."
    )

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        def _refresh_action_timings(entity: Stats) -> None:
            try:
                base = GAUGE_START / max(entity.spd, 1)
            except Exception:
                base = GAUGE_START
            entity.base_action_value = base
            entity.action_value = base

        async def _grant_speed_boost(ally: Stats) -> None:
            manager = getattr(ally, "effect_manager", None)
            if manager is None:
                manager = EffectManager(ally)
                ally.effect_manager = manager

            modifier = create_stat_buff(
                ally,
                name=f"{self.id}_spd_boost",
                turns=2,
                spd_mult=3.0,
            )

            _refresh_action_timings(ally)

            original_remove = modifier.remove

            def _remove_and_refresh() -> None:
                original_remove()
                _refresh_action_timings(ally)

            modifier.remove = _remove_and_refresh  # type: ignore[assignment]
            await manager.add_modifier(modifier)

            await BUS.emit_async(
                "card_effect",
                self.id,
                ally,
                "stat_buff_spd",
                200,
                {
                    "stat_affected": "spd",
                    "percentage_change": 200,
                    "turns": 2,
                    "new_modifier": modifier.id,
                },
            )
            await asyncio.sleep(0.002)

        def _battle_start(entity: Stats) -> None:
            if entity in party.members:
                safe_async_task(_grant_speed_boost(entity))

        self.subscribe("battle_start", _battle_start)
