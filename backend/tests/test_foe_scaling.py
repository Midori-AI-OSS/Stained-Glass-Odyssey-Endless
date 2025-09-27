import pytest

from autofighter.stats import Stats
from plugins.characters.foe_base import FoeBase


def test_level_up_increases_mitigation_and_vitality(monkeypatch):
    foe = FoeBase()
    base_mitigation = foe.mitigation
    base_vitality = foe.vitality
    called = False

    def stub(self):
        nonlocal called
        called = True

    monkeypatch.setattr(Stats, "_on_level_up", stub)
    foe._on_level_up()
    assert called
    assert foe.mitigation == pytest.approx(base_mitigation + 0.0001)
    assert foe.vitality == pytest.approx(base_vitality + 0.0001)

