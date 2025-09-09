from dataclasses import dataclass

from autofighter.effects import DamageOverTime
from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins import damage_effects
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Light(DamageTypeBase):
    """Supportive element that heals allies and purges harmful effects."""

    id: str = "Light"
    weakness: str = "Dark"
    color: tuple[int, int, int] = (255, 255, 255)

    def create_dot(self, damage: float, source) -> DamageOverTime | None:
        return damage_effects.create_dot(self.id, damage, source)

    async def on_action(self, actor, allies, enemies):
        for ally in allies:
            mgr = getattr(ally, "effect_manager", None)
            if mgr is not None:
                hot = damage_effects.create_hot(self.id, actor)
                if hot is not None:
                    mgr.add_hot(hot)
        for ally in allies:
            if ally.hp > 0 and ally.hp / ally.max_hp < 0.25:
                await ally.apply_healing(actor.atk, healer=actor)
                return False
        return True

    async def ultimate(self, actor, allies, enemies):
        """Fully heal allies, cleanse their DoTs, and weaken enemies."""
        if not getattr(actor, "use_ultimate", lambda: False)():
            return False
        for ally in allies:
            if ally.hp <= 0:
                continue
            mgr = getattr(ally, "effect_manager", None)
            if mgr is None:
                mgr = EffectManager(ally)
                ally.effect_manager = mgr

            # Remove all DoTs including Shadow Siphon
            for dot in list(mgr.dots):
                try:
                    mgr.dots.remove(dot)
                    ally.dots.remove(dot.id)
                except ValueError:
                    pass

            # Ensure Shadow Siphon is completely removed
            from plugins.damage_effects import SHADOW_SIPHON_ID

            try:
                if SHADOW_SIPHON_ID in ally.dots:
                    ally.dots.remove(SHADOW_SIPHON_ID)
                # Also remove from effect manager dots by id
                mgr.dots = [
                    d for d in mgr.dots if getattr(d, "id", "") != SHADOW_SIPHON_ID
                ]
            except (AttributeError, ValueError):
                pass

            missing = ally.max_hp - ally.hp
            if missing > 0:
                await ally.apply_healing(
                    missing,
                    healer=actor,
                    source_type="ultimate",
                    source_name="Light Ultimate",
                )
        for enemy in enemies:
            if enemy.hp <= 0:
                continue
            mgr = getattr(enemy, "effect_manager", None)
            if mgr is None:
                mgr = EffectManager(enemy)
                enemy.effect_manager = mgr
            mod = create_stat_buff(
                enemy,
                name="light_ultimate_def_down",
                turns=10,
                defense_mult=0.75,
            )
            mgr.add_modifier(mod)
        BUS.emit("light_ultimate", actor)
        return True

    @classmethod
    def get_ultimate_description(cls) -> str:
        return (
            "Removes all DoTs from allies—including Shadow Siphon—then heals them to full. "
            "Enemies receive a 25% defense debuff for 10 turns and a 'light_ultimate' event is emitted."
        )
