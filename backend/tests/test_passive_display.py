from autofighter.passives import PassiveRegistry
from autofighter.stats import Stats
from plugins.damage_types.generic import Generic


def _get_passive(description, pid):
    return next((p for p in description if p["id"] == pid), None)


def test_display_spinner():
    registry = PassiveRegistry()
    fighter = Stats(hp=100, damage_type=Generic())
    fighter.passives = ["player_level_up_bonus"]
    info = registry.describe(fighter)
    passive = _get_passive(info, "player_level_up_bonus")
    assert passive is not None
    assert passive["max_stacks"] == 1
    assert passive["display"] == "spinner"


def test_display_pips():
    registry = PassiveRegistry()
    fighter = Stats(hp=100, damage_type=Generic())
    fighter.passives = ["attack_up", "advanced_combat_synergy"]
    info = registry.describe(fighter)
    attack_up = _get_passive(info, "attack_up")
    assert attack_up is not None
    assert attack_up["max_stacks"] is None
    assert attack_up["display"] == "pips"

    synergy = _get_passive(info, "advanced_combat_synergy")
    assert synergy is not None
    assert synergy["max_stacks"] == 3
    assert synergy["display"] == "pips"


def test_display_number():
    registry = PassiveRegistry()
    fighter = Stats(hp=100, damage_type=Generic())
    fighter.passives = ["bubbles_bubble_burst"]
    info = registry.describe(fighter)
    passive = _get_passive(info, "bubbles_bubble_burst")
    assert passive is not None
    assert passive["max_stacks"] == 20
    assert passive["display"] == "number"


def test_luna_display_spinner_when_charged():
    registry = PassiveRegistry()
    fighter = Stats(hp=100, damage_type=Generic())
    fighter.passives = ["luna_lunar_reservoir"]
    # add charge above threshold
    from plugins.passives.normal.luna_lunar_reservoir import LunaLunarReservoir

    LunaLunarReservoir.add_charge(fighter, amount=2500)

    info = registry.describe(fighter)
    passive = _get_passive(info, "luna_lunar_reservoir")
    assert passive is not None
    assert passive["display"] == "spinner"
