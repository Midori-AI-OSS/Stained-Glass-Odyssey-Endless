import pytest

from autofighter.passives import PassiveRegistry
from plugins.players.carly import Carly


def test_carly_guardians_aegis_aggro():
    carly = Carly()
    registry = PassiveRegistry()
    registry.apply_aggro(carly)
    assert carly.aggro == pytest.approx(carly.base_aggro * 500, rel=1e-3)
