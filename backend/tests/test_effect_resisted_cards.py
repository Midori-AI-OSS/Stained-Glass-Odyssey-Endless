import asyncio
from types import SimpleNamespace
from unittest.mock import patch

from autofighter.effects import EffectManager
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.cards.calm_beads import CalmBeads
from plugins.cards.polished_shield import PolishedShield
from plugins.damage_types.fire import Fire


def _setup_ally_with_card(card_cls: type) -> tuple[asyncio.AbstractEventLoop, Stats]:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    ally = Stats()
    ally.id = "ally"
    ally.set_base_stat("max_hp", 100)
    ally.hp = ally.max_hp
    ally.set_base_stat("defense", 10)
    ally.set_base_stat("effect_resistance", 0.6)

    party = SimpleNamespace(members=[ally])
    loop.run_until_complete(card_cls().apply(party))

    if getattr(ally, "effect_manager", None) is None:
        ally.effect_manager = EffectManager(ally)

    return loop, ally


def _create_attacker() -> Stats:
    foe = Stats()
    foe.id = "foe"
    foe.set_base_stat("effect_hit_rate", 1.0)
    foe.change_damage_type(Fire())
    return foe


def _trigger_resist(target: Stats, attacker: Stats) -> None:
    manager = getattr(target, "effect_manager", None)
    if manager is None:
        manager = EffectManager(target)
        target.effect_manager = manager

    with patch("autofighter.effects.random.random", return_value=1.0):
        manager.maybe_inflict_dot(attacker, 100)


def test_calm_beads_grants_charge_on_resist():
    loop, ally = _setup_ally_with_card(CalmBeads)
    try:
        attacker = _create_attacker()
        baseline_charge = ally.ultimate_charge
        assert attacker.effect_hit_rate >= 0.99
        assert ally.effect_resistance > 0.5

        events: list[tuple[str | None, Stats, Stats, dict | None]] = []

        def _recorder(effect_name, target, source, details=None):
            events.append((effect_name, target, source, details))

        BUS.subscribe("effect_resisted", _recorder)
        try:
            BUS.set_async_preference(False)
            _trigger_resist(ally, attacker)
            loop.run_until_complete(asyncio.sleep(0.01))
        finally:
            BUS.set_async_preference(True)
            BUS.unsubscribe("effect_resisted", _recorder)

        assert not ally.effect_manager.dots
        assert events, "effect_resisted event did not fire"
        _, recorded_target, recorded_source, metadata = events[-1]
        assert recorded_target is ally
        assert recorded_source is attacker
        assert (metadata or {}).get("effect_type") == "dot"

        assert ally.ultimate_charge == baseline_charge + 1
        assert not ally.ultimate_ready
    finally:
        asyncio.set_event_loop(None)
        loop.close()


def test_polished_shield_grants_defense_on_resist():
    loop, ally = _setup_ally_with_card(PolishedShield)
    try:
        attacker = _create_attacker()
        baseline_defense = ally.defense
        assert attacker.effect_hit_rate >= 0.99
        assert ally.effect_resistance > 0.5

        events: list[tuple[str | None, Stats, Stats, dict | None]] = []

        def _recorder(effect_name, target, source, details=None):
            events.append((effect_name, target, source, details))

        BUS.subscribe("effect_resisted", _recorder)
        try:
            BUS.set_async_preference(False)
            _trigger_resist(ally, attacker)
            loop.run_until_complete(asyncio.sleep(0.01))
        finally:
            BUS.set_async_preference(True)
            BUS.unsubscribe("effect_resisted", _recorder)

        assert not ally.effect_manager.dots
        assert events, "effect_resisted event did not fire"

        assert ally.defense == baseline_defense + 3
        assert any(
            mod.name == "polished_shield_resist_def"
            for mod in ally.effect_manager.mods
        )
    finally:
        asyncio.set_event_loop(None)
        loop.close()
