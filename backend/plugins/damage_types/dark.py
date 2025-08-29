import asyncio
from dataclasses import dataclass

from autofighter.effects import DamageOverTime
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins import damage_effects
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Dark(DamageTypeBase):
    id: str = "Dark"
    weakness: str = "Light"
    color: tuple[int, int, int] = (145, 0, 145)
    ultimate_via_bus: bool = True

    _cleanup_registered: bool = False

    async def on_action(self, actor, allies, enemies) -> bool:
        for member in allies:
            mgr = getattr(member, "effect_manager", None)
            if mgr is not None:
                dmg = int(member.max_hp * 0.05)
                mgr.add_dot(damage_effects.create_shadow_siphon(dmg, actor))

        if not self._cleanup_registered:
            def _clear(_):
                sid = damage_effects.SHADOW_SIPHON_ID
                for member in allies:
                    member.dots = [d for d in member.dots if d != sid]
                    mgr = getattr(member, "effect_manager", None)
                    if mgr is not None:
                        mgr.dots = [d for d in mgr.dots if getattr(d, "id", "") != sid]
                self._cleanup_registered = False

            BUS.subscribe("battle_end", _clear)
            self._cleanup_registered = True

        return True

    def on_party_dot_damage_taken(self, damage, attacker, target) -> float:
        """Grant a tiny scaling bonus when Dark DoTs tick on allies.

        If the ticking DoT comes from a Dark attacker and the target is
        currently affected by Shadow Siphon, increase the attacker's
        offensive and defensive stats by a factor proportional to the
        damage dealt as a fraction of the target's max HP.

        The incoming ``damage`` value is returned unchanged; only the
        attacker is adjusted.
        """

        try:
            # Preconditions: source must be Dark and the target must have Shadow Siphon.
            if getattr(attacker, "damage_type", None) is not self:
                return damage

            if damage_effects.SHADOW_SIPHON_ID not in getattr(target, "dots", []):
                return damage

            # Compute damage as a fraction of max HP (guard against div-by-zero).
            max_hp = max(float(getattr(target, "max_hp", 0) or 0.0), 1.0)
            percent_of_max = max(float(damage) / max_hp, 0.0)

            # 0.05 per 1.0 (i.e., +5% when DoT equals 100% of max HP).
            scale = 1.0 + percent_of_max * 0.05

            # Apply scale to common stats via a temporary buff.
            mgr = getattr(attacker, "effect_manager", None)
            changes: dict[str, float] = {}
            if hasattr(attacker, "atk"):
                changes["atk_mult"] = scale
                changes["atk"] = 1
            if hasattr(attacker, "defense"):
                changes["defense_mult"] = scale
                changes["defense"] = 1
            if mgr is not None and changes:
                mod = create_stat_buff(attacker, turns=9999, **changes)
                mgr.add_modifier(mod)
        except Exception:
            # Intentionally swallow errors to avoid breaking combat flow.
            pass
        return damage

    async def ultimate(
        self,
        actor: Stats,
        allies: list[Stats],
        enemies: list[Stats],
    ) -> None:
        """Strike six times, scaling with allied DoT stacks.

        Damage is multiplied by ``1.75`` for every DoT stack present on the
        ``allies`` list (including the ``actor``).  Each of the six hits emits a
        ``damage`` event after applying damage.
        """

        if not enemies:
            return

        stacks = 0
        for member in allies:
            mgr = getattr(member, "effect_manager", None)
            if mgr is not None:
                stacks += len(getattr(mgr, "dots", []))
            else:
                stacks += len(getattr(member, "dots", []))

        multiplier = 1.75 ** stacks
        dmg = int(actor.atk * multiplier)
        target = enemies[0]
        for _ in range(6):
            dealt = await target.apply_damage(dmg, attacker=actor)
            BUS.emit("damage", actor, target, dealt)

    def create_dot(self, damage: float, source) -> DamageOverTime | None:
        return damage_effects.create_dot(self.id, damage, source)


def _ultimate_handler(user) -> None:
    dt = getattr(user, "damage_type", None)
    if not isinstance(dt, Dark):
        return
    allies = getattr(user, "allies", [])
    enemies = getattr(user, "enemies", [])
    loop = asyncio.get_event_loop()
    loop.create_task(dt.ultimate(user, allies, enemies))


BUS.subscribe("ultimate_used", _ultimate_handler)
