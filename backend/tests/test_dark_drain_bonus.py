import pytest

from autofighter.stats import Stats
from autofighter.stats import set_battle_active
import plugins.damage_types.dark as dark_module
from plugins.damage_types.dark import Dark


@pytest.mark.asyncio
async def test_dark_drain_multiplier_scales_with_total_drained(monkeypatch):
    dark = Dark()
    actor = Stats(damage_type=dark)
    ally_one = Stats()
    ally_two = Stats()

    actor.hp = 1000
    ally_one.hp = 500
    ally_two.hp = 250

    party = [actor, ally_one, ally_two]

    monkeypatch.setattr(dark_module.random, "uniform", lambda _a, _b: 1.0)

    set_battle_active(True)
    try:
        await dark.on_action(actor, party, [])
    finally:
        set_battle_active(False)

    bonus = getattr(actor, "_pending_dark_bonus", 1.0)
    assert bonus == pytest.approx(1.0175, rel=1e-6)

    assert actor.hp == 900
    assert ally_one.hp == 450
    assert ally_two.hp == 225
