import asyncio
from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class VitalCore(CardBase):
    id: str = "vital_core"
    name: str = "Vital Core"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"vitality": 0.03, "max_hp": 0.03})
    about: str = "+3% Vitality & +3% HP; When below 30% HP, gain +3% Vitality for 2 turns"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        loop = asyncio.get_running_loop()

        # Track which members have the vitality boost active to avoid stacking
        active_boosts = set()

        async def _check_low_hp() -> None:
            for member in party.members:
                member_id = id(member)
                current_hp = getattr(member, "hp", 0)
                max_hp = getattr(member, "max_hp", 1)

                if current_hp <= 0:
                    active_boosts.discard(member_id)
                    continue

                if current_hp / max_hp < 0.30 and member_id not in active_boosts:
                    active_boosts.add(member_id)

                    effect_manager = getattr(member, "effect_manager", None)
                    if effect_manager is None:
                        effect_manager = EffectManager(member)
                        member.effect_manager = effect_manager

                    vit_mod = create_stat_buff(
                        member,
                        name=f"{self.id}_low_hp_vit",
                        turns=2,
                        vitality_mult=1.03,
                    )
                    await effect_manager.add_modifier(vit_mod)

                    log = logging.getLogger(__name__)
                    log.debug(
                        "Vital Core activated vitality boost for %s: +3% vitality for 2 turns",
                        member.id,
                    )
                    await BUS.emit_async(
                        "card_effect",
                        self.id,
                        member,
                        "vitality_boost",
                        3,
                        {"vitality_boost": 3, "duration": 2, "trigger_threshold": 0.30},
                    )

                    def _remove_boost() -> None:
                        if member_id in active_boosts:
                            active_boosts.remove(member_id)

                    loop.call_soon_threadsafe(lambda: loop.call_later(20, _remove_boost))

        async def _on_damage_taken(target, attacker, damage, *_: object):
            await _check_low_hp()

        self.subscribe("turn_start", _check_low_hp)
        self.subscribe("damage_taken", _on_damage_taken)
