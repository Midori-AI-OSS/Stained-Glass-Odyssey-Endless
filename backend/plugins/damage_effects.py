from __future__ import annotations

from collections.abc import Callable
import logging

from autofighter.effects import DamageOverTime
from autofighter.effects import HealingOverTime
from plugins.dots.abyssal_corruption import AbyssalCorruption
from plugins.dots.blazing_torment import BlazingTorment
from plugins.dots.celestial_atrophy import CelestialAtrophy
from plugins.dots.charged_decay import ChargedDecay
from plugins.dots.frozen_wound import FrozenWound
from plugins.dots.gale_erosion import GaleErosion
from plugins.hots.radiant_regeneration import RadiantRegeneration

log = logging.getLogger(__name__)


def _set_source(effect: DamageOverTime | HealingOverTime, source) -> object:
    log.debug("Setting source %s on effect %s", source, effect.id)
    effect.source = source
    return effect


DOT_FACTORIES: dict[str, Callable[[float, object], DamageOverTime]] = {
    "Dark": lambda dmg, src: _set_source(AbyssalCorruption(int(dmg * 0.4), 3), src),
    "Fire": lambda dmg, src: _set_source(BlazingTorment(int(dmg * 0.5), 3), src),
    "Ice": lambda dmg, src: _set_source(FrozenWound(int(dmg * 0.25), 3), src),
    "Light": lambda dmg, src: _set_source(CelestialAtrophy(int(dmg * 0.3), 3), src),
    "Lightning": lambda dmg, src: _set_source(ChargedDecay(int(dmg * 0.25), 3), src),
    "Wind": lambda dmg, src: _set_source(GaleErosion(int(dmg * 0.25), 3), src),
}

HOT_FACTORIES: dict[str, Callable[[object], HealingOverTime]] = {
    "Light": lambda src: _set_source(RadiantRegeneration(), src),
}


def create_dot(damage_type: str, damage: float, source) -> DamageOverTime | None:
    log.debug("Creating DoT for type %s with damage %s", damage_type, damage)
    factory = DOT_FACTORIES.get(damage_type)
    if factory is None:
        log.debug("No DoT factory for type %s", damage_type)
        return None
    return factory(damage, source)


def create_hot(damage_type: str, source) -> HealingOverTime | None:
    log.debug("Creating HoT for type %s", damage_type)
    factory = HOT_FACTORIES.get(damage_type)
    if factory is None:
        log.debug("No HoT factory for type %s", damage_type)
        return None
    return factory(source)
