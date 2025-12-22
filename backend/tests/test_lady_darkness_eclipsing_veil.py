import pytest

from autofighter.stats import BUS, Stats
from plugins.passives.normal.lady_darkness_eclipsing_veil import (
    LadyDarknessEclipsingVeil,
)


def _reset_veil_state() -> None:
    LadyDarknessEclipsingVeil._attack_bonuses.clear()
    LadyDarknessEclipsingVeil._dot_callbacks.clear()
    LadyDarknessEclipsingVeil._resist_callbacks.clear()
    LadyDarknessEclipsingVeil._cleanup_callbacks.clear()
    LadyDarknessEclipsingVeil._party_cache.clear()


@pytest.mark.asyncio
async def test_eclipsing_veil_siphons_on_party_dot_ticks() -> None:
    _reset_veil_state()
    lady = Stats()
    lady.id = "lady_darkness"
    lady.passives = ["lady_darkness_eclipsing_veil"]
    lady.max_hp = 1000
    lady.hp = 600

    ally = Stats()
    ally.id = "ally"

    foe = Stats()
    foe.id = "foe"

    party = [lady, ally]

    passive = LadyDarknessEclipsingVeil()
    await passive.apply(lady, party=party)

    base_hp = lady.hp

    await BUS.emit_async("dot_tick", ally, foe, 200, "burn", {"effect_type": "dot"})
    assert lady.hp == base_hp + 2

    post_first = lady.hp
    await BUS.emit_async("dot_tick", foe, lady, 150, "bleed", {"effect_type": "dot"})
    assert lady.hp == post_first + 1

    outsider = Stats()
    outsider_target = Stats()
    await BUS.emit_async(
        "dot_tick",
        outsider,
        outsider_target,
        999,
        "burn",
        {"effect_type": "dot"},
    )
    assert lady.hp == post_first + 1  # unchanged by outsider event

    await BUS.emit_async("battle_end", lady)

    assert id(lady) not in LadyDarknessEclipsingVeil._dot_callbacks
    assert id(lady) not in LadyDarknessEclipsingVeil._party_cache


@pytest.mark.asyncio
async def test_eclipsing_veil_resist_grants_attack_bonus() -> None:
    _reset_veil_state()
    lady = Stats()
    lady.id = "lady_darkness"
    lady.passives = ["lady_darkness_eclipsing_veil"]

    ally = Stats()
    ally.id = "ally"

    foe = Stats()
    foe.id = "foe"

    passive = LadyDarknessEclipsingVeil()
    await passive.apply(lady, party=[lady, ally])

    base_atk = lady.atk
    await BUS.emit_async(
        "effect_resisted",
        "bleed",
        lady,
        foe,
        {"effect_type": "dot"},
    )

    expected_bonus = int(base_atk * 0.05)
    assert LadyDarknessEclipsingVeil.get_attack_bonus(lady) == expected_bonus

    effect_name = f"{LadyDarknessEclipsingVeil.id}_resist_bonus_{id(lady)}"
    effects = {effect.name: effect for effect in lady.get_active_effects()}
    assert effect_name in effects
    assert effects[effect_name].stat_modifiers["atk"] == expected_bonus

    await BUS.emit_async(
        "effect_resisted",
        "blessing",
        lady,
        foe,
        {"effect_type": "hot"},
    )
    assert LadyDarknessEclipsingVeil.get_attack_bonus(lady) == expected_bonus

    await BUS.emit_async("battle_end", lady)

    entity_id = id(lady)
    assert entity_id not in LadyDarknessEclipsingVeil._dot_callbacks
    assert entity_id not in LadyDarknessEclipsingVeil._resist_callbacks


@pytest.mark.asyncio
async def test_eclipsing_veil_reapply_preserves_attack_bonus() -> None:
    _reset_veil_state()
    lady = Stats()
    lady.id = "lady_darkness"
    lady.passives = ["lady_darkness_eclipsing_veil"]

    passive = LadyDarknessEclipsingVeil()
    await passive.apply(lady, party=[lady])

    await BUS.emit_async(
        "effect_resisted",
        "bleed",
        lady,
        None,
        {"effect_type": "dot"},
    )

    effect_name = f"{LadyDarknessEclipsingVeil.id}_resist_bonus_{id(lady)}"
    effects = [effect for effect in lady.get_active_effects() if effect.name == effect_name]
    assert len(effects) == 1
    first_bonus = effects[0].stat_modifiers["atk"]
    assert first_bonus == LadyDarknessEclipsingVeil.get_attack_bonus(lady)

    await passive.apply(lady, party=[lady])

    effects_after = [effect for effect in lady.get_active_effects() if effect.name == effect_name]
    assert len(effects_after) == 1
    assert effects_after[0].stat_modifiers["atk"] == first_bonus
    assert LadyDarknessEclipsingVeil.get_attack_bonus(lady) == first_bonus
