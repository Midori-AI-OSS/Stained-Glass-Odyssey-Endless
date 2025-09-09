import pytest

from autofighter.gacha.system import GachaConfig
from autofighter.gacha.system import GachaSystem


def test_pity_escalation_and_reset():
    config = GachaConfig(
        base_rate=0.0, pity_start=1, pity_increment=0.1, pity_threshold=3
    )
    system = GachaSystem(config)

    assert not system.pull(rng=lambda: 0.99)
    assert system.current_rate() == pytest.approx(0.1)
    assert not system.pull(rng=lambda: 0.99)
    assert system.current_rate() == pytest.approx(0.2)
    assert not system.pull(rng=lambda: 0.99)
    assert system.pity_counter == 3
    assert system.pull(rng=lambda: 0.99)
    assert system.pity_counter == 0


def test_state_persistence():
    config = GachaConfig(
        base_rate=0.0, pity_start=1, pity_increment=0.1, pity_threshold=3
    )
    system = GachaSystem(config)
    system.pull(rng=lambda: 0.99)
    state = system.to_dict()
    loaded = GachaSystem.from_dict(state)
    assert loaded.pity_counter == system.pity_counter
    assert loaded.config == system.config
    assert not loaded.pull(rng=lambda: 0.99)
    assert loaded.pity_counter == 2
