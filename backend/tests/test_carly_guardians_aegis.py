import pytest

from autofighter.passives import PassiveRegistry
from autofighter.stats import Stats
from plugins.passives.normal.carly_guardians_aegis import CarlyGuardiansAegis


@pytest.mark.asyncio
async def test_heals_most_injured_ally():
    registry = PassiveRegistry()
    carly = Stats()
    ally_low = Stats()
    ally_high = Stats()
    ally_low.hp = 400
    ally_high.hp = 700
    party = [carly, ally_low, ally_high]
    carly.passives = ["carly_guardians_aegis"]

    await registry.trigger_turn_start(carly, party=party, turn=1)

    heal_effects_low = [e for e in ally_low.get_active_effects() if e.name == "carly_guardians_aegis_defense_heal"]
    heal_effects_high = [e for e in ally_high.get_active_effects() if e.name == "carly_guardians_aegis_defense_heal"]
    assert heal_effects_low
    assert not heal_effects_high
    expected_heal = int(carly.defense * 0.1)
    assert ally_low.hp == 400 + expected_heal


@pytest.mark.asyncio
async def test_attack_growth_converts_to_defense_stacks():
    registry = PassiveRegistry()
    carly = Stats()
    carly.passives = ["carly_guardians_aegis"]
    baseline = carly.get_base_stat("atk")

    # Trigger once to record baseline
    await registry.trigger_turn_start(carly, party=[carly], turn=1)

    carly.modify_base_stat("atk", 100)  # growth of 100

    await registry.trigger_turn_start(carly, party=[carly], turn=2)

    assert carly.get_base_stat("atk") == baseline
    defense_effects = [e for e in carly.get_active_effects() if e.name == "carly_guardians_aegis_defense_stacks"]
    assert defense_effects
    assert defense_effects[0].stat_modifiers["defense"] == 75


@pytest.mark.asyncio
async def test_ultimate_distributes_mitigation():
    carly = Stats()
    ally1 = Stats()
    ally2 = Stats()
    party = [carly, ally1, ally2]
    passive = CarlyGuardiansAegis()

    await passive.on_ultimate_use(carly, party)

    for ally in (ally1, ally2):
        effects = [e for e in ally.get_active_effects() if e.name == "carly_guardians_aegis_shared_mitigation"]
        assert effects
        assert effects[0].stat_modifiers["mitigation"] == pytest.approx(0.25)

    reduction = [e for e in carly.get_active_effects() if e.name == "carly_guardians_aegis_mitigation_reduction"]
    assert reduction
    assert reduction[0].stat_modifiers["mitigation"] == pytest.approx(-0.5)


@pytest.mark.asyncio
async def test_carly_aegis_aggro_increase():
    registry = PassiveRegistry()
    carly = Stats()
    carly.passives = ["carly_guardians_aegis"]
    await registry.trigger("battle_start", carly)
    assert carly.aggro == pytest.approx(carly.base_aggro * 500)
