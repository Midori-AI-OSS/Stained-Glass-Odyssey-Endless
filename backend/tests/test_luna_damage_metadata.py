import pytest

from autofighter.stats import BUS
from autofighter.stats import Stats
from autofighter.stats import calc_animation_time
from autofighter.stats import set_battle_active
from plugins.characters import luna as luna_module
from plugins.characters.luna import Luna
from plugins.characters.luna import _LunaSwordCoordinator
from autofighter.rooms.battle.turn_loop.player_turn import (
    prepare_action_attack_metadata,
)


@pytest.mark.asyncio
async def test_luna_consecutive_hits_emit_unique_attack_metadata(monkeypatch):
    set_battle_active(True)
    events: list[tuple] = []

    def _capture(event: str, *args):
        if event == "damage_taken":
            events.append(args)

    monkeypatch.setattr(BUS, "emit_batched", _capture)

    attacker = Luna()
    attacker.id = "luna_test_attacker"
    attacker.set_base_stat("atk", 600)
    attacker.set_base_stat("crit_rate", 0)
    attacker.set_base_stat("crit_damage", 2)
    attacker.actions_per_turn = 2
    attacker.action_points = attacker.actions_per_turn

    target = Stats()
    target.id = "luna_test_target"
    target.set_base_stat("max_hp", 5000)
    target.set_base_stat("defense", 10)
    target.set_base_stat("dodge_odds", 0)
    target.hp = target.max_hp

    try:
        prepare_action_attack_metadata(attacker)
        await target.apply_damage(attacker.atk, attacker=attacker, action_name="Normal Attack")
        attacker.action_points = max(attacker.action_points - 1, 0)

        prepare_action_attack_metadata(attacker)
        await target.apply_damage(attacker.atk, attacker=attacker, action_name="Normal Attack")
    finally:
        set_battle_active(False)

    damage_events = [args for args in events if len(args) >= 8]
    assert len(damage_events) >= 2, "Expected at least two damage events from consecutive hits"

    first_details = damage_events[0][-1]
    second_details = damage_events[1][-1]

    assert first_details.get("attack_index") == 1
    assert first_details.get("attack_total") == 2
    assert second_details.get("attack_index") == 2
    assert second_details.get("attack_total") == 2
    assert first_details.get("attack_sequence") != second_details.get("attack_sequence")
    assert isinstance(first_details.get("attack_sequence"), int)
    assert isinstance(second_details.get("attack_sequence"), int)


def test_luna_animation_metadata_propagates_to_summons(monkeypatch):
    luna = Luna()

    assert calc_animation_time(luna, 1) > 0
    expected_multi_target = (
        luna.animation_duration
        + luna.animation_per_target * max(3 - 1, 0)
    )
    assert calc_animation_time(luna, 3) == pytest.approx(expected_multi_target)

    helper = _LunaSwordCoordinator(luna, None)

    class _StubSword:
        def __init__(self) -> None:
            self.actions_per_turn = 0
            self.tags = set()

    stub_sword = _StubSword()

    monkeypatch.setattr(luna_module, "_register_luna_sword", lambda *_, **__: None)

    try:
        helper.add_sword(stub_sword, "Lumen")
        assert stub_sword.animation_duration == pytest.approx(
            luna.animation_duration
        )
        assert stub_sword.animation_per_target == pytest.approx(
            luna.animation_per_target
        )
    finally:
        helper.detach()
