import asyncio

import pytest

from autofighter.cards import apply_cards
from autofighter.cards import award_card
from autofighter.effects import EffectManager
from autofighter.party import Party
from autofighter.stats import BUS
from autofighter.stats import Stats
import plugins.cards.steel_bangles as steel_bangles_module


@pytest.mark.asyncio
async def test_steel_bangles_applies_attack_debuff(monkeypatch) -> None:
    defender = Stats()
    attacker = Stats()
    party = Party([defender])

    # Initialize effect manager for the attacker (target of the debuff)
    attacker.effect_manager = EffectManager(attacker)

    award_card(party, "steel_bangles")
    await apply_cards(party)
    await asyncio.sleep(0)

    # Store original attack value
    original_attack = attacker.atk
    print(f"Original attack: {original_attack}")

    # Force damage reduction to trigger (100% chance)
    monkeypatch.setattr(steel_bangles_module.random, "random", lambda: 0.0)
    await BUS.emit_async("damage_dealt", defender, attacker, 100, "attack", None, None, "attack")
    await asyncio.sleep(0.1)

    # Check that attacker now has reduced attack
    new_attack = attacker.atk
    print(f"New attack: {new_attack}")
    print(f"Attack reduction: {original_attack - new_attack}")

    # We expect roughly a 3% reduction, but account for diminishing returns
    # Just verify that attack was reduced
    assert new_attack < original_attack, f"Attack should be reduced. Original: {original_attack}, New: {new_attack}"

    # Check that the effect has 1 turn duration
    assert len(attacker.effect_manager.mods) == 1
    modifier = attacker.effect_manager.mods[0]
    assert modifier.turns == 1
    assert modifier.name == "steel_bangles_attack_debuff"
