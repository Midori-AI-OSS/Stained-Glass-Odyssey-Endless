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

        async def _on_effect_applied(effect_name, entity, details=None):
            if not details or entity is None:
                return

            effect_type = details.get("effect_type")
            effect_id = details.get("effect_id")
            if effect_type not in {"dot", "stat_modifier"} or effect_id is None:
                return

            manager = getattr(entity, "effect_manager", None)
            if manager is None:
                return

            if effect_type == "dot":
                pool = manager.dots
            else:
                pool = manager.mods

            effect = next((eff for eff in reversed(pool) if getattr(eff, "id", None) == effect_id), None)
            if effect is None:
                return

            source = getattr(effect, "source", None)
            if source not in party.members:
                return

            if effect_type == "stat_modifier":
                deltas = details.get("deltas") or {}
                multipliers = details.get("multipliers") or {}
                has_negative_delta = any(value < 0 for value in deltas.values())
                has_reductive_multiplier = any(value < 1 for value in multipliers.values())
                if not (has_negative_delta or has_reductive_multiplier):
                    return

            source_id = id(source)
            current_stacks = crit_stacks.get(source_id, 0)
            if current_stacks >= 3:
                return

            new_stacks = current_stacks + 1
            crit_stacks[source_id] = new_stacks

            effect_manager = getattr(source, "effect_manager", None)
            if effect_manager is None:
                effect_manager = EffectManager(source)
                source.effect_manager = effect_manager

            crit_mod = create_stat_buff(
                source,
                name=f"{self.id}_debuff_crit_{new_stacks}",
                turns=1,
                crit_rate_mult=1 + (new_stacks * 0.01),
            )
            setattr(crit_mod, "source", source)
            await effect_manager.add_modifier(crit_mod)

            import logging

            log = logging.getLogger(__name__)
            log.debug(
                "Keen Goggles crit stack: %d stacks (+%d%% crit rate) for %s",
                new_stacks,
                new_stacks,
                getattr(source, "id", source_id),
            )
            await BUS.emit_async(
                "card_effect",
                self.id,
                source,
                "crit_stack",
                new_stacks,
                {
                    "stack_count": new_stacks,
                    "crit_rate_bonus": new_stacks,
                    "max_stacks": 3,
                    "trigger_event": "debuff_applied",
                },
            )

        def _on_action_used(actor, *_args):
            if actor in party.members:
                actor_id = id(actor)
                if actor_id in crit_stacks:
                    del crit_stacks[actor_id]

        self.subscribe("effect_applied", _on_effect_applied)
        self.subscribe("action_used", _on_action_used)
