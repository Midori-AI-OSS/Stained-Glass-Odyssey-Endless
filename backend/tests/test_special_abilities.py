"""Tests covering special ability plugins."""

from __future__ import annotations

import pytest

from autofighter.passives import PassiveRegistry
from autofighter.stats import Stats
from plugins.actions.context import BattleContext
from plugins.actions.registry import ActionRegistry
from plugins.actions.special.ally_overload_cascade import AllyOverloadCascade
from plugins.actions.special.carly_guardian_barrier import CarlyGuardianBarrier


def _battle_context(actor: Stats, allies: list[Stats], enemies: list[Stats]) -> BattleContext:
    """Create a minimal battle context for ability execution."""

    return BattleContext(
        turn=0,
        run_id="test",
        phase="player",
        actor=actor,
        allies=allies,
        enemies=enemies,
        action_registry=ActionRegistry(),
        passive_registry=PassiveRegistry(),
        effect_managers={},
        summon_manager=None,
        event_bus=None,
        enrage_state=None,
        visual_queue=None,
        damage_router=None,
    )


@pytest.mark.asyncio
async def test_special_ability_requires_matching_character() -> None:
    """SpecialAbilityBase only permits the configured character id."""

    actor = Stats()
    actor.id = "ally"
    actor.atk = 100
    foe = Stats()
    foe.id = "foe"
    foe.hp = 200
    foe.max_hp = 200
    context = _battle_context(actor, [actor], [foe])
    ability = AllyOverloadCascade()

    assert await ability.can_execute(actor, [foe], context)

    actor.id = "someone_else"
    assert not await ability.can_execute(actor, [foe], context)


@pytest.mark.asyncio
async def test_ally_overload_cascade_deals_damage() -> None:
    """Ally's ability damages up to two foes."""

    actor = Stats()
    actor.id = "ally"
    actor.atk = 150
    foe_a = Stats()
    foe_a.id = "foe_a"
    foe_a.hp = 300
    foe_a.max_hp = 300
    foe_b = Stats()
    foe_b.id = "foe_b"
    foe_b.hp = 300
    foe_b.max_hp = 300
    context = _battle_context(actor, [actor], [foe_a, foe_b])
    ability = AllyOverloadCascade()

    result = await ability.execute(actor, [foe_a, foe_b], context)

    assert result.success is True
    assert foe_a.hp < 300
    assert foe_b.hp < 300
    assert "foe_a" in result.damage_dealt
    assert "foe_b" in result.damage_dealt


@pytest.mark.asyncio
async def test_carly_guardian_barrier_heals_lowest_ally() -> None:
    """Carly's ability heals allies and applies a mitigation buff."""

    actor = Stats()
    actor.id = "carly"
    actor.defense = 250
    ally = Stats()
    ally.id = "ally"
    ally.hp = 200
    ally.max_hp = 400
    foes = [Stats()]
    foes[0].id = "foe"
    foes[0].hp = 400
    foes[0].max_hp = 400
    context = _battle_context(actor, [actor, ally], foes)
    ability = CarlyGuardianBarrier()

    result = await ability.execute(actor, [], context)

    assert result.success is True
    assert ally.hp > 200
    active_effects = [effect.name for effect in ally.get_active_effects()]
    assert any(name.endswith("mitigation") for name in active_effects)
