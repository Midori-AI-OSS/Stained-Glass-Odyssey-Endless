from dataclasses import dataclass
from typing import ClassVar

from autofighter.effects import DamageOverTime
from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins import damage_effects
from plugins.damage_types._base import DamageTypeBase


@dataclass
class Wind(DamageTypeBase):
    """Agile element that strikes in flurries and erodes defenses."""
    id: str = "Wind"
    weakness: str = "Lightning"
    color: tuple[int, int, int] = (0, 255, 0)
    _players: ClassVar[list] = []
    _foes: ClassVar[list] = []
    _pending: ClassVar[list] = []
    _initialized: ClassVar[bool] = False

    def __post_init__(self) -> None:
        # Ensure we only subscribe once at the class level
        if not Wind._initialized:
            BUS.subscribe("battle_start", Wind._on_battle_start)
            BUS.subscribe("battle_end", Wind._on_battle_end)
            Wind._initialized = True

    # Previous implementation scattered DoTs after an ultimate by moving
    # existing effects. The new design: when Wind uses its ultimate, strike
    # every living foe multiple times and temporarily increase the user's
    # effect hit rate so Gale Erosion applies more reliably. The number of hits
    # is derived dynamically (from actor.wind_ultimate_hits or actor.ultimate_hits)
    # to allow relics/cards to adjust it.

    def create_dot(self, damage: float, source) -> DamageOverTime | None:
        return damage_effects.create_dot(self.id, damage, source)

    async def ultimate(self, actor, allies, enemies):
        """Distribute attack across rapid hits on all foes."""
        from autofighter.rooms.battle.pacing import YIELD_MULTIPLIER
        from autofighter.rooms.battle.pacing import pace_sleep
        from autofighter.rooms.battle.targeting import select_aggro_target

        # Consume ultimate; bail if not ready
        if not await self.consume_ultimate(actor):
            return False

        actor_type = getattr(actor, "plugin_type", None)
        if actor_type == "player" and actor not in Wind._players:
            Wind._players.append(actor)
        elif actor_type == "foe" and actor not in Wind._foes:
            Wind._foes.append(actor)

        # Ensure the actor has an EffectManager so temporary buffs apply cleanly
        a_mgr = getattr(actor, "effect_manager", None)
        if a_mgr is None:
            a_mgr = EffectManager(actor)
            actor.effect_manager = a_mgr

        # Apply a short-lived boost to effect hit rate to increase Wind DoT odds
        eh_mod = create_stat_buff(
            actor,
            name="wind_ultimate_effect_hit",
            turns=1,
            effect_hit_rate_mult=1.5,
        )
        a_mgr.add_modifier(eh_mod)

        # Determine dynamic hit count (allow cards/relics to override via attributes)
        hits = int(getattr(actor, "wind_ultimate_hits", getattr(actor, "ultimate_hits", 25)) or 25)
        hits = max(1, hits)

        # Strike each living enemy with a total budget equal to actor.atk distributed
        # across all hits and all targets. This keeps Wind ultimate AoE damage in line
        # with single-target ults while preserving multi-hit feel.
        base = int(getattr(actor, "atk", 0))
        base = max(1, base)

        living = [foe for foe in enemies if getattr(foe, "hp", 0) > 0]
        if not living:
            return True
        total_chunks = hits * len(living)
        if total_chunks <= 0:
            return True
        per = base // total_chunks
        rem = base - per * total_chunks

        effect_managers: dict = {}
        for foe in living:
            f_mgr = getattr(foe, "effect_manager", None)
            if f_mgr is None:
                f_mgr = EffectManager(foe)
                foe.effect_manager = f_mgr
            effect_managers[foe] = f_mgr

        for _ in range(total_chunks):
            try:
                _, foe = select_aggro_target(enemies)
            except ValueError:
                break
            if getattr(foe, "hp", 0) <= 0:
                continue
            add_one = 1 if rem > 0 else 0
            per_hit = per + add_one
            if rem > 0:
                rem -= 1
            per_hit = max(1, int(per_hit))
            dmg = await foe.apply_damage(per_hit, attacker=actor, action_name="Wind Ultimate")
            await pace_sleep(YIELD_MULTIPLIER)
            try:
                await BUS.emit_async("hit_landed", actor, foe, dmg, "attack", "wind_ultimate")
            except Exception:
                pass
            try:
                effect_managers[foe].maybe_inflict_dot(actor, dmg)
            except Exception:
                pass

        # Clean up the temporary buff immediately after the sequence
        try:
            eh_mod.remove()
        except Exception:
            pass
        return True

    @classmethod
    def get_ultimate_description(cls) -> str:
        return (
            "Temporarily boosts the user's effect hit rate, then splits their attack "
            "into repeated strikes distributed across all living enemies. The number "
            "of hits derives from `wind_ultimate_hits` or `ultimate_hits` allowing "
            "relics and cards to modify it. Each hit respects TURN_PACING via the "
            "battle pacing helper."
        )

    @classmethod
    def _on_battle_start(cls, actor) -> None:
        """Register actors into appropriate lists when battle starts."""
        # Only register actors with Wind damage type
        actor_damage_type = getattr(actor, "damage_type", None)
        if not isinstance(actor_damage_type, Wind):
            return

        # Determine actor type and add to appropriate registry
        actor_type = getattr(actor, "plugin_type", None)
        if actor_type == "player":
            if actor not in cls._players:
                cls._players.append(actor)
        elif actor_type == "foe":
            if actor not in cls._foes:
                cls._foes.append(actor)

    @classmethod
    def _on_battle_end(cls, *_: object) -> None:
        """Clear all registries when battle ends."""
        cls._players.clear()
        cls._foes.clear()
        cls._pending.clear()
