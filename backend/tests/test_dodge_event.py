import pytest

from autofighter import stats as stats_module
from autofighter.party import Party
from autofighter.stats import Stats
from plugins.cards import lightweight_boots as lightweight_boots_module
from plugins.cards.lightweight_boots import LightweightBoots
from plugins.characters._base import PlayerBase
from plugins.event_bus import EventBus


@pytest.mark.asyncio
async def test_apply_damage_emits_dodge_event(monkeypatch):
    original_bus = stats_module.BUS
    bus = EventBus()
    stats_module.BUS = bus
    stats_module.set_battle_active(True)

    captured: list[dict[str, object]] = []

    async def _on_dodge(dodger, attacker, raw_amount, action_name, details):
        captured.append(
            {
                "dodger": dodger,
                "attacker": attacker,
                "raw_amount": raw_amount,
                "action_name": action_name,
                "details": details,
            }
        )

    bus.subscribe("dodge", _on_dodge)

    defender = Stats()
    defender.id = "defender"
    defender.set_base_stat("dodge_odds", 1.0)

    attacker = Stats()
    attacker.id = "attacker"

    monkeypatch.setattr(stats_module.random, "random", lambda: 0.0)

    try:
        dealt = await defender.apply_damage(250, attacker=attacker, action_name="slash")
    finally:
        stats_module.set_battle_active(False)
        stats_module.BUS = original_bus

    assert dealt == 0
    assert captured, "dodge event should be emitted"
    event = captured[0]
    assert event["dodger"] is defender
    assert event["attacker"] is attacker
    assert event["raw_amount"] == 250
    assert event["action_name"] == "slash"
    details = event["details"]
    assert isinstance(details, dict)
    assert details.get("dodger_id") == "defender"
    assert details.get("attacker_id") == "attacker"
    assert details.get("source") == "stats.apply_damage"


@pytest.mark.asyncio
async def test_lightweight_boots_heals_on_dodge(monkeypatch):
    original_bus = stats_module.BUS
    original_card_bus = lightweight_boots_module.BUS
    bus = EventBus()
    stats_module.BUS = bus
    lightweight_boots_module.BUS = bus
    stats_module.set_battle_active(True)

    events: list[tuple[str, int, dict[str, object]]] = []

    async def _on_card_effect(card_id, entity, effect_type, value, details):
        events.append((effect_type, value, details))

    bus.subscribe("card_effect", _on_card_effect)

    party = Party()
    dodger = PlayerBase()
    dodger.id = "dodger"
    dodger.set_base_stat("dodge_odds", 1.0)
    dodger.hp = dodger.max_hp - 100
    party.members.append(dodger)

    card = LightweightBoots()
    await card.apply(party)

    attacker = PlayerBase()
    attacker.id = "foe"

    monkeypatch.setattr(stats_module.random, "random", lambda: 0.0)

    initial_hp = dodger.hp
    expected_heal = int(dodger.max_hp * 0.02)

    try:
        damage = await dodger.apply_damage(400, attacker=attacker, action_name="thrust")
    finally:
        card.cleanup_subscriptions()
        stats_module.set_battle_active(False)
        stats_module.BUS = original_bus
        lightweight_boots_module.BUS = original_card_bus

    assert damage == 0
    assert dodger.hp == min(dodger.max_hp, initial_hp + expected_heal)

    dodge_heal_events = [evt for evt in events if evt[0] == "dodge_heal"]
    assert dodge_heal_events, "card should emit dodge_heal event"
    _, heal_amount, metadata = dodge_heal_events[-1]
    assert heal_amount == expected_heal
    assert metadata.get("heal_amount") == expected_heal
    assert metadata.get("trigger_event") == "dodge"
    assert metadata.get("raw_amount") == 400
    assert metadata.get("action_name") == "thrust"
