from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class TacticalKit(CardBase):
    id: str = "tactical_kit"
    name: str = "Tactical Kit"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"atk": 0.02, "max_hp": 0.02})
    about: str = "+2% ATK & +2% HP; Once per battle, convert 1% HP to +2% ATK for one action"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        # Track which members have used their tactical conversion
        conversion_used = set()

        async def _on_action_about_to_start(actor):
            # Check if actor is one of our party members and hasn't used conversion yet
            if actor in party.members:
                actor_id = id(actor)
                if actor_id not in conversion_used:
                    current_hp = getattr(actor, 'hp', 0)
                    max_hp = getattr(actor, 'max_hp', 1)

                    # Only convert if we have enough HP (at least 2% to be safe)
                    if current_hp / max_hp > 0.02:
                        # Mark as used
                        conversion_used.add(actor_id)

                        # Convert 1% HP to +2% ATK for one action
                        hp_to_convert = int(max_hp * 0.01)
                        if hasattr(actor, 'hp'):
                            actor.hp = max(1, actor.hp - hp_to_convert)

                        # Apply temporary ATK boost
                        effect_manager = getattr(actor, 'effect_manager', None)
                        if effect_manager is None:
                            effect_manager = EffectManager(actor)
                            actor.effect_manager = effect_manager

                        atk_mod = create_stat_buff(
                            actor,
                            name=f"{self.id}_hp_to_atk",
                            turns=1,
                            atk_mult=1.02  # +2% ATK
                        )
                        effect_manager.add_modifier(atk_mod)

                        import logging
                        log = logging.getLogger(__name__)
                        log.debug("Tactical Kit conversion: -%d HP for +2%% ATK to %s", hp_to_convert, actor.id)
                        await BUS.emit_async("card_effect", self.id, actor, "hp_to_atk_conversion", 2, {
                            "hp_converted": hp_to_convert,
                            "atk_bonus": 2,
                            "duration": 1,
                            "once_per_battle": True
                        })

        def _on_battle_start(target):
            # Reset conversion usage for new battle
            if target in party.members:
                conversion_used.clear()

        BUS.subscribe("action_start", _on_action_about_to_start)
        BUS.subscribe("battle_start", _on_battle_start)