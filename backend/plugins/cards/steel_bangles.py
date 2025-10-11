from dataclasses import dataclass
from dataclasses import field
import random

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class SteelBangles(CardBase):
    id: str = "steel_bangles"
    name: str = "Steel Bangles"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"mitigation": 0.03})
    about: str = "+3% Mitigation; On attack hit, 5% chance to reduce the target's next attack damage by 3%"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _on_damage_dealt(attacker, target, damage, damage_type, source, source_action, action_name, details=None):
            # Check if attacker is one of our party members and this is an attack
            if attacker in party.members and action_name == "attack":
                # 5% chance to reduce target's next attack damage by 3%
                if random.random() < 0.05:
                    # Apply attack debuff to the target using effect manager
                    effect_manager = getattr(target, 'effect_manager', None)
                    if effect_manager is None:
                        effect_manager = EffectManager(target)
                        target.effect_manager = effect_manager

                    # Create attack debuff: 3% damage reduction = 0.97x attack multiplier
                    attack_debuff = create_stat_buff(
                        target,
                        name=f"{self.id}_attack_debuff",
                        turns=1,  # Lasts for 1 turn
                        atk_mult=0.97,  # 3% damage reduction
                    )
                    await effect_manager.add_modifier(attack_debuff)

                    import logging
                    log = logging.getLogger(__name__)
                    log.debug("Steel Bangles attack debuff applied to %s", getattr(target, 'id', 'unknown'))
                    await BUS.emit_async("card_effect", self.id, attacker, "attack_debuff_applied", 3, {
                        "damage_reduction": 3,
                        "target": getattr(target, 'id', 'unknown'),
                        "trigger_chance": 0.05
                    })

        self.subscribe("damage_dealt", _on_damage_dealt)
