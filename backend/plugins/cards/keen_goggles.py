from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class KeenGoggles(CardBase):
    id: str = "keen_goggles"
    name: str = "Keen Goggles"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"crit_rate": 0.03, "effect_hit_rate": 0.03})
    about: str = "+3% Crit Rate & +3% Effect Hit Rate; Landing a debuff grants +1% crit rate for next action (stack up to 3)"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        # Track stacks per party member
        crit_stacks = {}

        async def _on_effect_applied(target, effect_name, duration, source):
            # Check if source is one of our party members and effect is a debuff
            if source in party.members:
                effect_lower = effect_name.lower()
                is_debuff = any(keyword in effect_lower for keyword in
                               ['bleed', 'poison', 'burn', 'freeze', 'stun', 'silence', 'slow', 'weakness', 'curse'])

                if is_debuff:
                    source_id = id(source)
                    current_stacks = crit_stacks.get(source_id, 0)

                    # Stack up to 3
                    if current_stacks < 3:
                        new_stacks = current_stacks + 1
                        crit_stacks[source_id] = new_stacks

                        # Apply temporary crit rate buff for next action
                        effect_manager = getattr(source, 'effect_manager', None)
                        if effect_manager is None:
                            effect_manager = EffectManager(source)
                            source.effect_manager = effect_manager

                        # Create temporary crit rate buff
                        crit_mod = create_stat_buff(
                            source,
                            name=f"{self.id}_debuff_crit_{new_stacks}",
                            turns=1,
                            crit_rate_mult=1 + (new_stacks * 0.01)  # +1% per stack
                        )
                        effect_manager.add_modifier(crit_mod)

                        import logging
                        log = logging.getLogger(__name__)
                        log.debug("Keen Goggles crit stack: %d stacks (+%d%% crit rate) for %s", new_stacks, new_stacks, source.id)
                        await BUS.emit_async("card_effect", self.id, source, "crit_stack", new_stacks, {
                            "stack_count": new_stacks,
                            "crit_rate_bonus": new_stacks,
                            "max_stacks": 3,
                            "trigger_event": "debuff_applied"
                        })

        def _on_action_taken(actor):
            # Reset stacks after action is taken
            if actor in party.members:
                actor_id = id(actor)
                if actor_id in crit_stacks:
                    del crit_stacks[actor_id]

        BUS.subscribe("effect_applied", _on_effect_applied)
        BUS.subscribe("action_taken", _on_action_taken)

        def _cleanup(*_: object) -> None:
            BUS.unsubscribe("effect_applied", _on_effect_applied)
            BUS.unsubscribe("action_taken", _on_action_taken)
            BUS.unsubscribe("battle_end", _cleanup)

        BUS.subscribe("battle_end", _cleanup)