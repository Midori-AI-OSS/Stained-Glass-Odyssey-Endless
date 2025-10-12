import asyncio
from dataclasses import dataclass
import math

from autofighter.effects import DamageOverTime
from autofighter.effects import EffectManager
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins import damage_effects
from plugins.damage_types._base import DamageTypeBase
from plugins.event_bus import bus as _event_bus


@dataclass
class Fire(DamageTypeBase):
    """Aggressive element that amplifies damage as the user weakens.

    Fire attacks scale with missing HP and often inflict burning damage over
    time at the cost of self-inflicted drain.
    """
    id: str = "Fire"
    weakness: str = "Ice"
    color: tuple[int, int, int] = (255, 0, 0)

    _drain_stacks: int = 0

    def __post_init__(self) -> None:
        BUS.subscribe("ultimate_used", self._on_ultimate_used)
        BUS.subscribe("turn_start", self._on_turn_start)
        BUS.subscribe("battle_end", self._on_battle_end)

    def create_dot(self, damage: float, source) -> DamageOverTime | None:
        return damage_effects.create_dot(self.id, damage, source)

    def on_damage(self, damage: float, attacker: Stats, target: Stats) -> float:
        if attacker.max_hp <= 0:
            return damage
        missing_ratio = 1 - (attacker.hp / attacker.max_hp)
        dmg = damage * (1 + missing_ratio)
        if self._drain_stacks > 0:
            dmg *= math.sqrt(5)
        return dmg

    async def ultimate(self, actor: Stats, allies: list[Stats], enemies: list[Stats]) -> bool:
        """Blast all foes for the caster's attack and try to ignite them."""
        from autofighter.rooms.battle.pacing import YIELD_MULTIPLIER
        from autofighter.rooms.battle.pacing import pace_sleep
        from autofighter.rooms.battle.targeting import select_aggro_target

        await super().ultimate(actor, allies, enemies)
        base = getattr(actor, "atk", 0)
        if base <= 0:
            return True
        hit_count = sum(1 for foe in enemies if getattr(foe, "hp", 0) > 0)
        for _ in range(hit_count):
            try:
                _, foe = select_aggro_target(enemies)
            except ValueError:
                break
            dealt = await foe.apply_damage(base, attacker=actor, action_name="Fire Ultimate")
            await pace_sleep(YIELD_MULTIPLIER)
            mgr = getattr(foe, "effect_manager", None)
            if mgr is None:
                mgr = EffectManager(foe)
                foe.effect_manager = mgr
            try:
                await mgr.maybe_inflict_dot(actor, dealt)
            except Exception:
                pass
        return True

    def _on_ultimate_used(self, user: Stats) -> None:
        if getattr(user, "damage_type", None) is not self:
            return
        self._drain_stacks += 1

    def _on_turn_start(self, actor: Stats) -> None:
        if self._drain_stacks <= 0:
            return
        if getattr(actor, "damage_type", None) is not self:
            return
        dmg = actor.max_hp * 0.05 * self._drain_stacks
        if dmg > 0:
            pre = math.sqrt(dmg)
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                asyncio.run(actor.apply_damage(pre))
                _event_bus._process_batches_sync()
            else:
                loop.create_task(actor.apply_damage(pre))

    def _on_battle_end(self, *_: object) -> None:
        self._drain_stacks = 0
        BUS.unsubscribe("ultimate_used", self._on_ultimate_used)
        BUS.unsubscribe("turn_start", self._on_turn_start)
        BUS.unsubscribe("battle_end", self._on_battle_end)

    @classmethod
    def get_ultimate_description(cls) -> str:
        return (
            "Deals the user's attack as damage to every living enemy and rolls "
            "Blazing Torment on each. Every use adds a drain stack that burns "
            "the caster for 5% of max HP per stack at the start of their turns. "
            "Ultimate hits use the pacing helper so TURN_PACING tweaks apply."
        )
