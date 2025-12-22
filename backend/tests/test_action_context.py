"""Tests for BattleContext helper methods."""

from __future__ import annotations

import asyncio
import contextlib

import pytest

from autofighter.effects import EffectManager
from autofighter.stats import BUS, Stats, get_enrage_percent, set_enrage_percent
from plugins.actions.context import BattleContext
from plugins.actions.registry import ActionRegistry
from plugins.event_bus import bus


@pytest.fixture
def mock_actor() -> Stats:
    """Create a mock actor for testing."""
    actor = Stats()
    actor.id = "test_actor"
    actor.hp = 100
    actor.max_hp = 100
    actor.atk = 10
    actor.defense = 5
    actor.action_points = 3
    actor.ultimate_charge = 0
    return actor


@pytest.fixture
def mock_target() -> Stats:
    """Create a mock target for testing."""
    target = Stats()
    target.id = "test_target"
    target.hp = 80
    target.max_hp = 80
    target.atk = 8
    target.defense = 4
    target.dodge_odds = 0.0  # Disable dodge for deterministic tests
    return target


@pytest.fixture
def battle_context(mock_actor: Stats, mock_target: Stats) -> BattleContext:
    """Create a minimal battle context for testing."""
    from autofighter import stats as stats_module
    from autofighter.passives import PassiveRegistry

    # Set battle as active
    stats_module._BATTLE_ACTIVE = True

    context = BattleContext(
        turn=1,
        run_id="test_run",
        phase="player",
        actor=mock_actor,
        allies=[mock_actor],
        enemies=[mock_target],
        action_registry=ActionRegistry(),
        passive_registry=PassiveRegistry(),
        effect_managers={},
    )

    yield context

    # Clean up - set battle as inactive
    stats_module._BATTLE_ACTIVE = False


@pytest.mark.asyncio
async def test_battle_context_apply_damage(
    battle_context: BattleContext,
    mock_actor: Stats,
    mock_target: Stats,
) -> None:
    """Test that BattleContext.apply_damage works correctly."""
    initial_hp = mock_target.hp
    damage_amount = 20.0

    damage_dealt = await battle_context.apply_damage(
        mock_actor,
        mock_target,
        damage_amount,
    )

    assert damage_dealt > 0
    assert mock_target.hp < initial_hp


@pytest.mark.asyncio
async def test_battle_context_apply_damage_with_metadata(
    battle_context: BattleContext,
    mock_actor: Stats,
    mock_target: Stats,
) -> None:
    """Test that metadata is properly staged for damage application."""
    metadata = {
        "attack_index": 1,
        "attack_total": 1,
        "attack_sequence": 1,
        "action_name": "Test Attack",
    }

    damage_dealt = await battle_context.apply_damage(
        mock_actor,
        mock_target,
        15.0,
        metadata=metadata,
    )

    assert damage_dealt > 0


@pytest.mark.asyncio
async def test_battle_context_apply_healing_matches_stats_pipeline(
    battle_context: BattleContext,
    mock_actor: Stats,
    mock_target: Stats,
) -> None:
    """Healing through the context should mirror direct Stats.apply_healing."""

    previous_enrage = get_enrage_percent()
    events: list[tuple[str, tuple]] = []

    def _heal_received(*args) -> None:  # noqa: ANN002
        events.append(("heal_received", args))

    def _heal(*args) -> None:  # noqa: ANN002
        events.append(("heal", args))

    baseline_target = Stats()
    baseline_target.hp = 40
    baseline_target.max_hp = 100
    baseline_target.vitality = 1.5
    baseline_target.id = "baseline_target"

    baseline_healer = Stats()
    baseline_healer.vitality = 1.2
    baseline_healer.id = "baseline_healer"

    mock_target.hp = 40
    mock_target.max_hp = 100
    mock_target.vitality = 1.5
    mock_actor.vitality = 1.2

    set_enrage_percent(0.25)

    expected = await baseline_target.apply_healing(
        20,
        healer=baseline_healer,
        source_type="skill",
        source_name="Test Skill",
    )
    expected_hp = baseline_target.hp

    if bus._batch_timer is not None:  # noqa: SLF001
        with contextlib.suppress(asyncio.CancelledError):
            await bus._batch_timer
    if bus._batched_events:  # noqa: SLF001
        await bus._process_batches_internal()  # noqa: SLF001

    try:
        BUS.subscribe("heal_received", _heal_received)
        BUS.subscribe("heal", _heal)

        healed = await battle_context.apply_healing(
            mock_actor,
            mock_target,
            20,
            source_type="skill",
            source_name="Test Skill",
        )

        if bus._batch_timer is not None:  # noqa: SLF001
            with contextlib.suppress(asyncio.CancelledError):
                await bus._batch_timer
        if bus._batched_events:  # noqa: SLF001
            await bus._process_batches_internal()  # noqa: SLF001
        await asyncio.sleep(0)
    finally:
        set_enrage_percent(previous_enrage)
        BUS.unsubscribe("heal_received", _heal_received)
        BUS.unsubscribe("heal", _heal)

    assert healed == expected
    assert mock_target.hp == expected_hp
    assert len(events) == 2
    event_types = {event[0] for event in events}
    assert {"heal_received", "heal"} == event_types

    received_event = next(event for event in events if event[0] == "heal_received")
    heal_event = next(event for event in events if event[0] == "heal")

    assert received_event[1][0] is mock_target
    assert heal_event[1][0] is mock_actor
    assert received_event[1][2] == expected
    assert heal_event[1][2] == expected


@pytest.mark.asyncio
async def test_battle_context_apply_healing_overheal_matches_shields(
    battle_context: BattleContext,
    mock_actor: Stats,
    mock_target: Stats,
) -> None:
    """Overheal flag should mirror shield conversion from Stats.apply_healing."""

    mock_target.hp = 95
    mock_target.max_hp = 100
    mock_target.overheal_enabled = False
    mock_target.shields = 0

    baseline_target = Stats()
    baseline_target.hp = 95
    baseline_target.max_hp = 100
    baseline_target.shields = 0
    baseline_target.enable_overheal()

    expected = await baseline_target.apply_healing(
        20,
        healer=mock_actor,
        source_type="test",
        source_name="overheal-check",
    )

    healed = await battle_context.apply_healing(
        mock_actor,
        mock_target,
        20,
        overheal_allowed=True,
        source_type="test",
        source_name="overheal-check",
    )

    assert healed == expected
    assert mock_target.hp == baseline_target.hp
    assert mock_target.shields == baseline_target.shields
    assert mock_target.overheal_enabled is False


def test_battle_context_spend_resource_ultimate_charge(
    battle_context: BattleContext,
    mock_actor: Stats,
) -> None:
    """Test spending ultimate charge resource."""
    mock_actor.ultimate_charge = 100

    battle_context.spend_resource(mock_actor, "ultimate_charge", 50)

    assert mock_actor.ultimate_charge == 50


def test_battle_context_spend_resource_action_points(
    battle_context: BattleContext,
    mock_actor: Stats,
) -> None:
    """Test spending action points resource."""
    mock_actor.action_points = 3

    battle_context.spend_resource(mock_actor, "action_points", 1)

    assert mock_actor.action_points == 2


def test_battle_context_allies_of(
    battle_context: BattleContext,
    mock_actor: Stats,
) -> None:
    """Test that allies_of returns correct list."""
    allies = battle_context.allies_of(mock_actor)

    assert mock_actor in allies
    assert len(allies) == 1


def test_battle_context_enemies_of(
    battle_context: BattleContext,
    mock_actor: Stats,
    mock_target: Stats,
) -> None:
    """Test that enemies_of returns correct list."""
    enemies = battle_context.enemies_of(mock_actor)

    assert mock_target in enemies
    assert len(enemies) == 1


def test_battle_context_effect_manager_for(
    battle_context: BattleContext,
    mock_target: Stats,
) -> None:
    """Test that effect_manager_for creates or retrieves managers."""
    manager1 = battle_context.effect_manager_for(mock_target)

    assert isinstance(manager1, EffectManager)

    # Second call should return cached manager
    manager2 = battle_context.effect_manager_for(mock_target)
    assert manager1 is manager2
