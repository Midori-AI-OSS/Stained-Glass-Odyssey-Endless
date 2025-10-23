"""Tests for Soul Prism relic - revival mechanics."""
import asyncio
import sys
import types

from autofighter.party import Party
from autofighter.stats import BUS
from plugins.characters._base import PlayerBase
from plugins.characters.foe_base import FoeBase
from plugins.relics.soul_prism import SoulPrism


def setup_event_loop():
    """Set up an event loop for testing."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def test_soul_prism_revives_ally_without_effect_manager():
    """Test that Soul Prism can revive allies that never had an effect manager."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    # Create a fallen ally without effect_manager
    fallen_member = PlayerBase()
    fallen_member.id = "fallen_ally"
    fallen_member.set_base_stat("max_hp", 100)
    fallen_member.hp = 0  # Dead
    # Intentionally do NOT create effect_manager
    party.members.append(fallen_member)

    # Add Soul Prism relic
    party.relics.append("soul_prism")

    # Apply the relic
    relic = SoulPrism()
    loop.run_until_complete(relic.apply(party))

    # Create a foe to trigger battle_end event
    foe = FoeBase()
    foe.id = "test_foe"
    foe.set_base_stat("max_hp", 100)
    foe.hp = 100

    # Emit battle_end event which should trigger revival
    loop.run_until_complete(BUS.emit_async("battle_end", foe))

    # Give time for async handlers to complete
    loop.run_until_complete(asyncio.sleep(0.1))

    # Check that ally was revived
    assert fallen_member.hp > 0, "Ally should be revived with HP > 0"
    assert hasattr(fallen_member, "effect_manager"), "Effect manager should be created"
    assert fallen_member.effect_manager is not None, "Effect manager should not be None"


def test_soul_prism_revives_ally_with_existing_effect_manager():
    """Test that Soul Prism works correctly with allies that already have an effect manager."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    # Create a fallen ally with effect_manager
    from autofighter.effects import EffectManager
    fallen_member = PlayerBase()
    fallen_member.id = "fallen_ally_with_mgr"
    fallen_member.set_base_stat("max_hp", 100)
    fallen_member.hp = 0  # Dead
    fallen_member.effect_manager = EffectManager(fallen_member)
    party.members.append(fallen_member)

    # Add Soul Prism relic
    party.relics.append("soul_prism")

    # Apply the relic
    relic = SoulPrism()
    loop.run_until_complete(relic.apply(party))

    # Create a foe to trigger battle_end event
    foe = FoeBase()
    foe.id = "test_foe"
    foe.set_base_stat("max_hp", 100)
    foe.hp = 100

    # Emit battle_end event which should trigger revival
    loop.run_until_complete(BUS.emit_async("battle_end", foe))

    # Give time for async handlers to complete
    loop.run_until_complete(asyncio.sleep(0.1))

    # Check that ally was revived
    assert fallen_member.hp > 0, "Ally should be revived with HP > 0"
    assert fallen_member.effect_manager is not None, "Effect manager should still exist"


def test_soul_prism_does_not_affect_living_allies():
    """Test that Soul Prism doesn't affect allies with HP > 0."""
    sys.modules.setdefault(
        "llms.torch_checker", types.SimpleNamespace(is_torch_available=lambda: False)
    )

    loop = setup_event_loop()
    party = Party()

    # Create a living ally
    living_member = PlayerBase()
    living_member.id = "living_ally"
    living_member.set_base_stat("max_hp", 100)
    living_member.hp = 50  # Alive
    party.members.append(living_member)

    # Add Soul Prism relic
    party.relics.append("soul_prism")

    # Apply the relic
    relic = SoulPrism()
    loop.run_until_complete(relic.apply(party))

    # Create a foe to trigger battle_end event
    foe = FoeBase()
    foe.id = "test_foe"
    foe.set_base_stat("max_hp", 100)
    foe.hp = 100

    # Record HP before battle_end
    hp_before = living_member.hp

    # Emit battle_end event
    loop.run_until_complete(BUS.emit_async("battle_end", foe))

    # Give time for async handlers to complete
    loop.run_until_complete(asyncio.sleep(0.1))

    # Check that living ally's HP wasn't changed
    assert living_member.hp == hp_before, "Living ally's HP should not change"
