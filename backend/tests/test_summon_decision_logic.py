"""Tests for summon decision logic and AI behavior."""

from llms import torch_checker
import pytest

from autofighter.summons import Summon
from autofighter.summons import SummonManager
from plugins.players.ally import Ally


@pytest.mark.asyncio
async def test_summon_viability_evaluation(monkeypatch):
    """Test the summon viability evaluation logic."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    SummonManager.cleanup()

    # Create a test summon
    summoner = Ally()
    summoner.id = "test_summoner"
    summoner._base_atk = 100
    summoner._base_max_hp = 200
    summoner._base_defense = 50

    summon = Summon.create_from_summoner(
        summoner=summoner,
        summon_type="test",
        source="test_source",
        stat_multiplier=0.5,
        turns_remaining=5,
    )

    # Test healthy summon
    summon.hp = summon.max_hp  # Full health
    eval_result = SummonManager.evaluate_summon_viability(summon)

    assert eval_result["viable"] is True
    assert eval_result["health_good"] is True
    assert eval_result["expiring_soon"] is False
    assert eval_result["time_remaining"] == 5
    assert "keep current summon" in eval_result["recommendation"].lower()

    # Test low health summon
    summon.hp = int(summon.max_hp * 0.1)  # 10% health
    eval_result = SummonManager.evaluate_summon_viability(summon)

    assert eval_result["viable"] is False
    assert eval_result["health_good"] is False
    assert "low health" in eval_result["recommendation"].lower()

    # Test expiring summon
    summon.hp = summon.max_hp  # Full health
    summon.turns_remaining = 1  # Expiring soon
    eval_result = SummonManager.evaluate_summon_viability(summon)

    assert eval_result["viable"] is False
    assert eval_result["expiring_soon"] is True
    assert "expiring" in eval_result["recommendation"].lower()


@pytest.mark.asyncio
async def test_resummon_decision_logic(monkeypatch):
    """Test the decision logic for when to resummon."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    SummonManager.cleanup()

    summoner = Ally()
    summoner.id = "test_summoner"
    summoner._base_atk = 100
    summoner._base_max_hp = 200
    summoner._base_defense = 50

    # Test no existing summons - should resummon
    decision = SummonManager.should_resummon("test_summoner")
    assert decision["should_resummon"] is True
    assert "no existing summons" in decision["reason"].lower()
    assert decision["viable_count"] == 0

    # Create a healthy summon
    summon = SummonManager.create_summon(
        summoner=summoner, summon_type="test", source="test_source", turns_remaining=10
    )
    summon.hp = summon.max_hp  # Ensure full health

    # Test with healthy summon - should NOT resummon
    decision = SummonManager.should_resummon("test_summoner")
    assert decision["should_resummon"] is False
    assert "viable summon" in decision["reason"].lower()
    assert decision["viable_count"] == 1

    # Damage the summon to low health
    summon.hp = int(summon.max_hp * 0.1)  # 10% health

    # Test with damaged summon - should resummon
    decision = SummonManager.should_resummon("test_summoner")
    assert decision["should_resummon"] is True
    assert "low health" in decision["reason"].lower()
    assert decision["viable_count"] == 0


@pytest.mark.asyncio
async def test_smart_summon_creation(monkeypatch):
    """Test that summon creation respects decision logic."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    SummonManager.cleanup()

    summoner = Ally()
    summoner.id = "test_summoner"
    summoner._base_atk = 100
    summoner._base_max_hp = 200
    summoner._base_defense = 50

    # Create first summon (should succeed)
    summon1 = SummonManager.create_summon(
        summoner=summoner, summon_type="test1", source="test_source", max_summons=1
    )
    assert summon1 is not None
    summon1.hp = summon1.max_hp  # Ensure healthy

    # Try to create second summon with healthy first summon (should fail due to smart logic)
    summon2 = SummonManager.create_summon(
        summoner=summoner, summon_type="test2", source="test_source", max_summons=1
    )
    assert summon2 is None  # Should be blocked by smart logic

    # Damage the first summon
    summon1.hp = int(summon1.max_hp * 0.1)  # 10% health

    # Try to create second summon with damaged first summon (should succeed and replace)
    summon3 = SummonManager.create_summon(
        summoner=summoner, summon_type="test3", source="test_source", max_summons=1
    )
    assert summon3 is not None  # Should succeed because first summon is low health

    # Should have replaced the old summon
    active_summons = SummonManager.get_summons("test_summoner")
    assert len(active_summons) == 1
    assert active_summons[0].summon_type == "test3"


@pytest.mark.asyncio
async def test_force_create_bypasses_logic(monkeypatch):
    """Test that force_create bypasses smart decision logic."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    SummonManager.cleanup()

    summoner = Ally()
    summoner.id = "test_summoner"
    summoner._base_atk = 100
    summoner._base_max_hp = 200
    summoner._base_defense = 50

    # Create first summon
    summon1 = SummonManager.create_summon(
        summoner=summoner, summon_type="test1", source="test_source", max_summons=1
    )
    assert summon1 is not None
    summon1.hp = summon1.max_hp  # Ensure healthy

    # Force create second summon even with healthy first summon
    summon2 = SummonManager.create_summon(
        summoner=summoner,
        summon_type="test2",
        source="test_source",
        max_summons=1,
        force_create=True,
    )
    assert summon2 is not None  # Should succeed due to force_create

    # Should have replaced the old summon
    active_summons = SummonManager.get_summons("test_summoner")
    assert len(active_summons) == 1
    assert active_summons[0].summon_type == "test2"


@pytest.mark.asyncio
async def test_health_threshold_customization(monkeypatch):
    """Test that health threshold can be customized."""
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)

    SummonManager.cleanup()

    summoner = Ally()
    summoner.id = "test_summoner"
    summoner._base_atk = 100
    summoner._base_max_hp = 200
    summoner._base_defense = 50

    # Create summon with 40% health
    summon = SummonManager.create_summon(
        summoner=summoner, summon_type="test", source="test_source"
    )
    summon.hp = int(summon.max_hp * 0.4)  # 40% health

    # With default threshold (25%), should NOT resummon
    decision = SummonManager.should_resummon("test_summoner")
    assert decision["should_resummon"] is False

    # With higher threshold (50%), should resummon
    decision = SummonManager.should_resummon("test_summoner", min_health_threshold=0.5)
    assert decision["should_resummon"] is True
    assert decision["viable_count"] == 0
