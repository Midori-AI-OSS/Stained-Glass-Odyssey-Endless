import random

import pytest

from autofighter.passives import PassiveRegistry
from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.stats import set_battle_active
from plugins.damage_types.generic import Generic


class Actor(Stats):
    plugin_type = "player"
    async def use_ultimate(self) -> bool:  # pragma: no cover - simple helper
        if not self.ultimate_ready:
            return False
        self.ultimate_charge = 0
        self.ultimate_ready = False
        await BUS.emit_async("ultimate_used", self)
        return True


@pytest.mark.asyncio
async def test_generic_ultimate_hits_and_passive_triggers():
    registry = PassiveRegistry()
    llr = registry._registry["luna_lunar_reservoir"]
    llr._charge_points.clear()

    actor = Actor(damage_type=Generic(), passives=["luna_lunar_reservoir"])
    actor.id = "luna"
    actor._base_atk = 64
    actor._base_defense = 0
    actor._base_crit_rate = 0

    target = Stats()
    target.id = "target"
    target._base_defense = 0
    target.set_base_stat('dodge_odds', 0)

    actor.ultimate_charge = actor.ultimate_charge_max
    actor.ultimate_ready = True

    hits = {"count": 0}

    def count_hit(*_args):
        hits["count"] += 1

    BUS.subscribe("hit_landed", count_hit)
    try:
        result = await actor.damage_type.ultimate(actor, [actor], [target])
    finally:
        BUS.unsubscribe("hit_landed", count_hit)

    assert result is True
    assert hits["count"] == 64
    assert llr.get_charge(actor) == 64


@pytest.mark.asyncio
async def test_generic_ultimate_foe_targets_opponents():
    foe = Actor(damage_type=Generic())
    foe.plugin_type = "foe"
    foe.id = "foe"
    foe.atk = 640
    foe.defense = 0
    foe.set_base_stat("dodge_odds", 0.0)

    foe_buddy = Stats()
    foe_buddy.id = "foe_buddy"
    foe_buddy.set_base_stat("dodge_odds", 0.0)

    player_target = Stats()
    player_target.id = "player"
    player_target.defense = 0
    player_target.set_base_stat("dodge_odds", 0.0)

    foe.ultimate_charge = foe.ultimate_charge_max
    foe.ultimate_ready = True

    allies = [foe, foe_buddy]
    enemies = [player_target]

    player_start = player_target.hp
    foe_start = foe.hp

    set_battle_active(True)
    try:
        result = await foe.damage_type.ultimate(foe, allies, enemies)
    finally:
        set_battle_active(False)

    assert result is True
    assert player_target.hp < player_start
    assert foe.hp == foe_start


@pytest.mark.asyncio
async def test_generic_ultimate_prefers_high_aggro_target():
    random.seed(1337)

    actor = Actor(damage_type=Generic())
    actor.id = "generic-actor"
    actor._base_atk = 640
    actor._base_defense = 0
    actor.set_base_stat("dodge_odds", 0)
    actor.ultimate_charge = actor.ultimate_charge_max
    actor.ultimate_ready = True

    foes: list[Stats] = []
    for idx, aggro in enumerate((1.0, 2.5, 7.5)):
        foe = Stats()
        foe.id = f"foe-{idx}"
        foe._base_defense = 0
        foe.set_base_stat("dodge_odds", 0.0)
        foe.base_aggro = aggro
        foes.append(foe)

    hits: dict[str, int] = {}

    async def record_hit(*args) -> None:
        target = args[1]
        hits[target.id] = hits.get(target.id, 0) + 1

    BUS.subscribe("hit_landed", record_hit)
    try:
        await actor.damage_type.ultimate(actor, [actor], foes)
    finally:
        BUS.unsubscribe("hit_landed", record_hit)

    assert sum(hits.values()) == 64
    assert hits.get("foe-2", 0) > hits.get("foe-1", 0) >= hits.get("foe-0", 0)
