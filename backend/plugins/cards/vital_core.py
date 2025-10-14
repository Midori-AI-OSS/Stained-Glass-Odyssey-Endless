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

        # Track which members have the vitality boost active to avoid stacking
        active_boosts: dict[int, str] = {}

        async def _check_low_hp() -> None:
            for member in party.members:
                current_hp = getattr(member, "hp", 0)
                max_hp = getattr(member, "max_hp", 0)
                member_key = id(member)

                if max_hp <= 0:
                    active_boosts.pop(member_key, None)
                    continue

                if current_hp <= 0:
                    active_boosts.pop(member_key, None)
                    continue

                if current_hp / max_hp >= 0.30:
                    continue

                if member_key in active_boosts:
                    continue

                effect_manager = getattr(member, "effect_manager", None)
                if effect_manager is None:
                    effect_manager = EffectManager(member)
                    member.effect_manager = effect_manager

                effect_id = f"{self.id}_low_hp_vit_{member_key}"
                vit_mod = create_stat_buff(
                    member,
                    name=f"{self.id}_low_hp_vit",
                    id=effect_id,
                    turns=2,
                    vitality_mult=1.03,
                )
                await effect_manager.add_modifier(vit_mod)

                active_boosts[member_key] = effect_id

                log = logging.getLogger(__name__)
                log.debug(
                    "Vital Core activated vitality boost for %s: +3% vitality for 2 turns",
                    getattr(member, "id", "member"),
                )
                await BUS.emit_async(
                    "card_effect",
                    self.id,
                    member,
                    "vitality_boost",
                    3,
                    {"vitality_boost": 3, "duration": 2, "trigger_threshold": 0.30},
                )

        async def _on_damage_taken(target, attacker, damage, *_: object):
            await _check_low_hp()

        async def _on_effect_expired(effect_name, target, payload):
            if payload.get("effect_type") != "stat_modifier":
                return

            effect_id = payload.get("effect_id")
            member_key = id(target)

            if effect_id is None:
                return

            if active_boosts.get(member_key) != effect_id:
                return

            active_boosts.pop(member_key, None)
            await _check_low_hp()

        async def _on_entity_defeat(target, *_: object):
            active_boosts.pop(id(target), None)

        async def _on_battle_end(*_: object):
            active_boosts.clear()

        self.subscribe("turn_start", _check_low_hp)
        self.subscribe("damage_taken", _on_damage_taken)
        self.subscribe("effect_expired", _on_effect_expired)
        self.subscribe("entity_defeat", _on_entity_defeat)
        self.subscribe("battle_end", _on_battle_end, cleanup_event=None)
