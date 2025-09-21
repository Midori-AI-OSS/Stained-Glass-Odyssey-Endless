import contextlib
from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class SwiftFootwork(CardBase):
    id: str = "swift_footwork"
    name: str = "Swift Footwork"
    stars: int = 2
    effects: dict[str, float] = field(default_factory=lambda: {"spd": 0.2})
    about: str = (
        "Permanent +20% SPD; on battle start gain +30% SPD for two turns."
    )

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)
        burst_id = f"{self.id}_spd_burst"

        async def _battle_start(*_args) -> None:
            for member in party.members:
                mgr = getattr(member, "effect_manager", None)
                if mgr is None:
                    mgr = EffectManager(member)
                    member.effect_manager = mgr

                for mod in list(getattr(mgr, "mods", [])):
                    if getattr(mod, "id", "") != burst_id:
                        continue

                    with contextlib.suppress(Exception):
                        mod.remove()

                    with contextlib.suppress(ValueError):
                        mgr.mods.remove(mod)

                mods_list = getattr(member, "mods", None)
                if isinstance(mods_list, list):
                    mods_list[:] = [mid for mid in mods_list if mid != burst_id]

                burst = create_stat_buff(
                    member,
                    name=burst_id,
                    turns=2,
                    spd_mult=1.3,
                )
                mgr.add_modifier(burst)
                await BUS.emit_async(
                    "card_effect",
                    self.id,
                    member,
                    "battle_start_spd_burst",
                    30,
                    {
                        "stat_affected": "spd",
                        "percentage_change": 30.0,
                        "duration": 2,
                    },
                )

        BUS.subscribe("battle_start", _battle_start)

        async def _battle_end(*_args) -> None:
            for member in party.members:
                mgr = getattr(member, "effect_manager", None)
                if mgr is None:
                    continue

                for mod in list(getattr(mgr, "mods", [])):
                    if getattr(mod, "id", "") != burst_id:
                        continue

                    with contextlib.suppress(Exception):
                        mod.remove()

                    with contextlib.suppress(ValueError):
                        mgr.mods.remove(mod)

                mods_list = getattr(member, "mods", None)
                if isinstance(mods_list, list):
                    mods_list[:] = [mid for mid in mods_list if mid != burst_id]

            BUS.unsubscribe("battle_start", _battle_start)
            BUS.unsubscribe("battle_end", _battle_end)

        BUS.subscribe("battle_end", _battle_end)

