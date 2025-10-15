import asyncio
import sys
import types

from autofighter.party import Party
from autofighter.relics import apply_relics
from autofighter.relics import award_relic
from autofighter.stats import BUS
from plugins.characters._base import PlayerBase


def setup_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


def test_featherweight_anklet_grants_permanent_spd():
    """Test that Featherweight Anklet grants permanent SPD boost."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member = PlayerBase()
    member.id = "test_member"
    member.set_base_stat("max_hp", 1000)
    member.set_base_stat("spd", 100)
    member.hp = 1000
    party.members.append(member)

    # Award and apply Featherweight Anklet
    award_relic(party, "featherweight_anklet")
    loop.run_until_complete(apply_relics(party))

    # Verify permanent SPD buff was applied (+2% = 1.02x)
    assert member.spd >= 102, f"Expected SPD >= 102, got {member.spd}"

    loop.run_until_complete(BUS.emit_async("battle_end", member))
    loop.close()


def test_featherweight_anklet_grants_first_action_burst():
    """Test that Featherweight Anklet grants SPD burst on first action."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member = PlayerBase()
    member.id = "test_member"
    member.set_base_stat("max_hp", 1000)
    member.set_base_stat("spd", 100)
    member.hp = 1000
    party.members.append(member)

    award_relic(party, "featherweight_anklet")
    loop.run_until_complete(apply_relics(party))

    # Start battle
    loop.run_until_complete(BUS.emit_async("battle_start"))

    # Get SPD after permanent buff
    spd_after_permanent = member.spd

    # Trigger first action
    loop.run_until_complete(BUS.emit_async("action_used", member))

    # SPD should increase with burst (+6% for 1 turn)
    spd_after_burst = member.spd
    assert (
        spd_after_burst > spd_after_permanent
    ), f"Expected burst SPD {spd_after_burst} > permanent {spd_after_permanent}"

    # Verify effect manager was created with the burst buff
    effect_manager = getattr(member, "effect_manager", None)
    assert effect_manager is not None, "Effect manager should be created"

    loop.run_until_complete(BUS.emit_async("battle_end", member))
    loop.close()


def test_featherweight_anklet_only_triggers_once_per_battle():
    """Test that Featherweight Anklet only triggers once per ally per battle."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member = PlayerBase()
    member.id = "test_member"
    member.set_base_stat("max_hp", 1000)
    member.set_base_stat("spd", 100)
    member.hp = 1000
    party.members.append(member)

    award_relic(party, "featherweight_anklet")
    loop.run_until_complete(apply_relics(party))

    # Start battle
    loop.run_until_complete(BUS.emit_async("battle_start"))

    # Trigger first action
    loop.run_until_complete(BUS.emit_async("action_used", member))

    effect_manager = getattr(member, "effect_manager", None)
    assert effect_manager is not None

    # Count modifiers after first action
    first_action_mod_count = len(effect_manager.mods)

    # Trigger second action - should NOT grant another burst
    loop.run_until_complete(BUS.emit_async("action_used", member))

    # Modifier count should not increase
    second_action_mod_count = len(effect_manager.mods)
    assert (
        second_action_mod_count == first_action_mod_count
    ), "Should not grant burst on second action"

    loop.run_until_complete(BUS.emit_async("battle_end", member))
    loop.close()


def test_featherweight_anklet_resets_between_battles():
    """Test that Featherweight Anklet activation tracking resets between battles."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member = PlayerBase()
    member.id = "test_member"
    member.set_base_stat("max_hp", 1000)
    member.set_base_stat("spd", 100)
    member.hp = 1000
    party.members.append(member)

    award_relic(party, "featherweight_anklet")

    # First battle
    loop.run_until_complete(apply_relics(party))
    loop.run_until_complete(BUS.emit_async("battle_start"))
    loop.run_until_complete(BUS.emit_async("action_used", member))

    # Verify first battle activation
    state_first = getattr(party, "_featherweight_anklet_state", None)
    assert state_first is not None
    assert (
        len(state_first["activated"]) == 1
    ), "Should have one activation in first battle"

    loop.run_until_complete(BUS.emit_async("battle_end", member))

    # Second battle - apply relics again (simulates new battle setup)
    loop.run_until_complete(apply_relics(party))
    loop.run_until_complete(BUS.emit_async("battle_start"))

    # Verify activation tracking was reset
    state_second = getattr(party, "_featherweight_anklet_state", None)
    assert state_second is not None
    assert (
        len(state_second["activated"]) == 0
    ), "Activation tracking should reset in new battle"

    # Should be able to trigger again
    loop.run_until_complete(BUS.emit_async("action_used", member))
    assert (
        len(state_second["activated"]) == 1
    ), "Should activate again in second battle"

    loop.run_until_complete(BUS.emit_async("battle_end", member))
    loop.close()


def test_featherweight_anklet_multiple_stacks():
    """Test that Featherweight Anklet stacks multiply permanent bonus and add burst bonus."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member = PlayerBase()
    member.id = "test_member"
    member.set_base_stat("max_hp", 1000)
    member.set_base_stat("spd", 100)
    member.hp = 1000
    party.members.append(member)

    # Award 2 stacks
    award_relic(party, "featherweight_anklet")
    award_relic(party, "featherweight_anklet")
    loop.run_until_complete(apply_relics(party))

    # With 2 stacks: permanent = (1.02)^2 = 1.0404 = +4.04%
    # So SPD should be about 100 * 1.0404 = 104.04
    assert member.spd >= 104, f"Expected SPD >= 104 with 2 stacks, got {member.spd}"

    # Start battle and trigger first action
    loop.run_until_complete(BUS.emit_async("battle_start"))
    spd_after_permanent = member.spd

    loop.run_until_complete(BUS.emit_async("action_used", member))

    # Burst bonus should be +6% * 2 = +12%
    spd_after_burst = member.spd
    assert (
        spd_after_burst > spd_after_permanent
    ), "Burst should further increase SPD with multiple stacks"

    loop.run_until_complete(BUS.emit_async("battle_end", member))
    loop.close()


def test_featherweight_anklet_multiple_allies():
    """Test that Featherweight Anklet tracks first action independently for each ally."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    member1 = PlayerBase()
    member1.id = "member1"
    member1.set_base_stat("max_hp", 1000)
    member1.set_base_stat("spd", 100)
    member1.hp = 1000
    party.members.append(member1)

    member2 = PlayerBase()
    member2.id = "member2"
    member2.set_base_stat("max_hp", 1000)
    member2.set_base_stat("spd", 100)
    member2.hp = 1000
    party.members.append(member2)

    award_relic(party, "featherweight_anklet")
    loop.run_until_complete(apply_relics(party))

    # Start battle
    loop.run_until_complete(BUS.emit_async("battle_start"))

    # Member1 acts first
    loop.run_until_complete(BUS.emit_async("action_used", member1))
    effect_manager1 = getattr(member1, "effect_manager", None)
    assert effect_manager1 is not None, "Member1 should have effect manager"

    # Member2 acts - should also get burst
    loop.run_until_complete(BUS.emit_async("action_used", member2))
    effect_manager2 = getattr(member2, "effect_manager", None)
    assert effect_manager2 is not None, "Member2 should have effect manager"

    # Member1 acts again - should NOT get another burst
    initial_mod_count_1 = len(effect_manager1.mods)
    loop.run_until_complete(BUS.emit_async("action_used", member1))
    assert len(effect_manager1.mods) == initial_mod_count_1, (
        "Member1 should not get burst on second action"
    )

    loop.run_until_complete(BUS.emit_async("battle_end", member1))
    loop.close()
