import asyncio
from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.stats import BUS
from plugins.cards._base import CardBase

log = logging.getLogger(__name__)


@dataclass
class HonedPoint(CardBase):
    id: str = "honed_point"
    name: str = "Honed Point"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"atk": 0.04})
    about: str = "+4% ATK; First attack vs an unmarked enemy deals +10% bonus damage"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        marked_enemies: dict[int, set[int]] = {}

        async def _on_damage_dealt(attacker, target, damage, _damage_type, source, source_action, action_name, details=None):
            if attacker in party.members and action_name == "attack":
                attacker_id = id(attacker)
                target_id = id(target)

                if attacker_id not in marked_enemies:
                    marked_enemies[attacker_id] = set()

                if target_id not in marked_enemies[attacker_id]:
                    marked_enemies[attacker_id].add(target_id)

                    bonus_damage = int(damage * 0.10)
                    if bonus_damage > 0:
                        asyncio.create_task(
                            target.apply_damage(
                                bonus_damage,
                                attacker,
                                action_name="honed_point_bonus",
                            )
                        )
                        log.debug(
                            "Honed Point bonus damage: +%d vs unmarked enemy", bonus_damage
                        )
                        await BUS.emit_async(
                            "card_effect",
                            self.id,
                            attacker,
                            "bonus_damage",
                            bonus_damage,
                            {
                                "bonus_damage": bonus_damage,
                                "trigger_event": "first_attack_unmarked",
                            },
                        )

        def _on_battle_start(target):
            if target in party.members:
                marked_enemies.clear()

        self.subscribe("damage_dealt", _on_damage_dealt)
        self.subscribe("battle_start", _on_battle_start)
