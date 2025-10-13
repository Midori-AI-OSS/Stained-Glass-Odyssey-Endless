import pytest

from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.damage_types.generic import Generic
from plugins.passives.normal.casno_phoenix_respite import CasnoPhoenixRespite


class DummyEffectManager:
    """Minimal effect manager for intercept helper testing."""

    def __init__(self, owner: Stats) -> None:
        self.owner = owner
        self.hots: list = []

    async def add_hot(self, hot) -> None:  # pragma: no cover - exercised via passive
        self.hots.append(hot)
        self.owner.hots.append(getattr(hot, "id", ""))


def _reset_passive_state() -> None:
    for handler in CasnoPhoenixRespite._battle_end_handlers.values():
        try:
            BUS.unsubscribe("battle_end", handler)
        except Exception:
            pass
    CasnoPhoenixRespite._battle_end_handlers.clear()
    CasnoPhoenixRespite._helper_effect_ids.clear()
    CasnoPhoenixRespite._pending_relaxed.clear()
    CasnoPhoenixRespite._attack_counts.clear()
    CasnoPhoenixRespite._relaxed_stacks.clear()
    CasnoPhoenixRespite._relaxed_converted.clear()


async def _perform_actions(passive: CasnoPhoenixRespite, target: Stats, count: int) -> None:
    for _ in range(count):
        await passive.apply(target)


@pytest.mark.asyncio
async def test_casno_relaxed_stacks_cycle_and_buffs() -> None:
    """Relaxed stacks should accumulate, trigger at >50, and buff stats at 15% per stack spent."""

    _reset_passive_state()

    casno = Stats(hp=1200, damage_type=Generic())
    casno.effect_manager = DummyEffectManager(casno)
    casno.passives = ["casno_phoenix_respite"]
    casno.action_points = 3

    # Configure recognizable base stats for buff validation.
    casno.max_hp = 1500
    casno.hp = 1500
    casno.atk = 100
    casno.defense = 80
    casno.crit_rate = 0.10
    casno.crit_damage = 1.80
    casno.effect_hit_rate = 1.25
    casno.effect_resistance = 0.20
    casno.mitigation = 1.50
    casno.vitality = 1.10
    casno.regain = 140
    casno.dodge_odds = 0.12
    casno.spd = 4

    passive = CasnoPhoenixRespite()

    # Build Relaxed stacks in five-attack increments.
    await _perform_actions(passive, casno, 5)
    assert CasnoPhoenixRespite.get_stacks(casno) == 1

    await _perform_actions(passive, casno, 245)  # 250 total actions -> 50 stacks
    assert CasnoPhoenixRespite.get_stacks(casno) == 50

    # Push past the Relaxed threshold and ensure the helper schedules.
    await _perform_actions(passive, casno, 5)
    assert CasnoPhoenixRespite.get_stacks(casno) == 51

    entity_id = id(casno)
    assert CasnoPhoenixRespite._pending_relaxed.get(entity_id) is True
    assert casno.effect_manager.hots, "Relaxed helper should be active once stacks exceed 50."

    helper = casno.effect_manager.hots[0]
    casno.hp = 600
    await helper.on_action(casno)

    # Action skipped, healed to full, and Relaxed stacks consumed.
    assert casno.action_points == 2
    assert casno.hp == casno.max_hp
    assert CasnoPhoenixRespite.get_stacks(casno) == 46
    assert CasnoPhoenixRespite._relaxed_converted.get(entity_id) == 5

    effect_name = CasnoPhoenixRespite._boost_effect_name(entity_id)
    boost_effect = next(e for e in casno.get_active_effects() if e.name == effect_name)
    assert boost_effect.stat_modifiers["atk"] == int(100 * 0.75)
    assert boost_effect.stat_modifiers["defense"] == int(80 * 0.75)
    assert boost_effect.stat_modifiers["crit_rate"] == pytest.approx(0.10 * 0.75)
    assert boost_effect.stat_modifiers["mitigation"] == pytest.approx(1.50 * 0.75)

    # Accumulate Relaxed stacks again to verify ongoing growth and buff scaling.
    await _perform_actions(passive, casno, 25)  # 5 more stacks -> exceeds 50 again
    assert CasnoPhoenixRespite.get_stacks(casno) == 51
    helper_two = casno.effect_manager.hots[0]
    casno.hp = 700
    casno.action_points = 5
    await helper_two.on_action(casno)

    assert casno.hp == casno.max_hp
    assert casno.action_points == 4
    assert CasnoPhoenixRespite.get_stacks(casno) == 46
    assert CasnoPhoenixRespite._relaxed_converted.get(entity_id) == 10

    updated_effect = next(e for e in casno.get_active_effects() if e.name == effect_name)
    assert updated_effect.stat_modifiers["atk"] == int(100 * 0.15 * 10)
    assert updated_effect.stat_modifiers["defense"] == int(80 * 0.15 * 10)
    assert updated_effect.stat_modifiers["crit_rate"] == pytest.approx(0.10 * 0.15 * 10)
    assert updated_effect.stat_modifiers["mitigation"] == pytest.approx(1.50 * 0.15 * 10)

    CasnoPhoenixRespite._clear_pending_state(casno)
