import asyncio

from autofighter.effects import DamageOverTime
from autofighter.effects import EffectManager
from autofighter.effects import HealingOverTime
from autofighter.rooms.utils import _serialize
from autofighter.stats import Stats


def test_serialize_effect_details():
    target = Stats()
    target.id = "t"
    mgr = EffectManager(target)
    target.effect_manager = mgr

    source = Stats()
    source.id = "s"
    asyncio.run(mgr.add_dot(DamageOverTime("burn", 5, 2, "burn", source)))
    asyncio.run(mgr.add_dot(DamageOverTime("burn", 5, 1, "burn", source)))
    asyncio.run(mgr.add_hot(HealingOverTime("regen", 3, 1, "regen", source)))

    target.passives = ["attack_up", "luna_lunar_reservoir", "luna_lunar_reservoir"]

    data = _serialize(target)

    assert data["dots"] == [
        {
            "id": "burn",
            "name": "burn",
            "damage": 5,
            "turns": 2,
            "source": "s",
            "element": "Generic",
            "stacks": 2,
        }
    ]
    assert data["hots"] == [
        {
            "id": "regen",
            "name": "regen",
            "healing": 3,
            "turns": 1,
            "source": "s",
            "element": "Generic",
            "stacks": 1,
        }
    ]
    assert any(
        p["id"] == "attack_up" and p["stacks"] == 1 and p["max_stacks"] is None
        for p in data["passives"]
    )
    assert any(
        p["id"] == "luna_lunar_reservoir" and p["stacks"] == 0 and p["max_stacks"] == 2000
        for p in data["passives"]
    )
    assert all("name" in p for p in data["passives"])
