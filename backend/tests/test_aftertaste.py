import pytest

from autofighter.stats import Stats
from plugins.effects.aftertaste import Aftertaste


def test_aftertaste_damage_range(monkeypatch):
    at = Aftertaste()
    monkeypatch.setattr(at.rng, "uniform", lambda a, b: 0.1)
    assert at.rolls() == [2]
    monkeypatch.setattr(at.rng, "uniform", lambda a, b: 1.5)
    assert at.rolls() == [37]


@pytest.mark.asyncio
async def test_aftertaste_multi_hit(monkeypatch):
    seq = iter([0.1, 0.5, 1.5])
    at = Aftertaste(hits=3)
    monkeypatch.setattr(at.rng, "uniform", lambda a, b: next(seq))

    applied = []

    async def fake_apply_damage(
        self, amount, attacker=None, *, trigger_on_hit=True, action_name=None
    ):
        applied.append(amount)
        return amount

    monkeypatch.setattr(Stats, "apply_damage", fake_apply_damage, raising=False)

    attacker = Stats()
    target = Stats()
    result = await at.apply(attacker, target)

    assert applied == [2, 12, 37]
    assert result == [2, 12, 37]
