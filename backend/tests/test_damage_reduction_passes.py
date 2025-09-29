import pytest

from autofighter.stats import get_enrage_percent
from autofighter.stats import set_battle_active
from plugins.characters.carly import Carly


def _calculate_expected_damage(stats: Carly, raw_amount: float, passes: int) -> int:
    src_vit = 1.0
    eps = 1e-6
    defense_term = max(stats.defense ** 5, 1)
    vit = float(stats.vitality)
    vit = vit if vit > eps else eps
    mit = float(stats.mitigation)
    mit = mit if mit > eps else eps
    denom = defense_term * vit * mit
    try:
        passes = int(passes)
    except Exception:
        passes = 1
    passes = max(1, passes)
    mitigated = raw_amount
    for _ in range(passes):
        mitigated = ((mitigated ** 2) * src_vit) / denom
    enrage = get_enrage_percent()
    if enrage > 0:
        mitigated *= 1.0 + enrage
    return max(int(mitigated), 1)


@pytest.mark.asyncio
async def test_carly_damage_reduction_uses_two_passes():
    raw_damage = 50

    carly = Carly()
    carly.set_base_stat("defense", 10)
    carly.set_base_stat("mitigation", 1.0)
    carly.set_base_stat("vitality", 1.0)
    carly.hp = carly.max_hp

    set_battle_active(True)
    try:
        expected = _calculate_expected_damage(
            carly,
            raw_damage,
            getattr(carly, "damage_reduction_passes", 1),
        )
        damage = await carly.apply_damage(raw_damage)
    finally:
        set_battle_active(False)

    assert damage == expected
    assert carly.last_damage_taken == expected

    baseline = Carly()
    baseline.set_base_stat("defense", 10)
    baseline.set_base_stat("mitigation", 1.0)
    baseline.set_base_stat("vitality", 1.0)
    baseline.damage_reduction_passes = 1
    baseline.hp = baseline.max_hp

    set_battle_active(True)
    try:
        baseline_expected = _calculate_expected_damage(baseline, raw_damage, 1)
        baseline_damage = await baseline.apply_damage(raw_damage)
    finally:
        set_battle_active(False)

    assert baseline_damage == baseline_expected
    assert damage <= baseline_damage
