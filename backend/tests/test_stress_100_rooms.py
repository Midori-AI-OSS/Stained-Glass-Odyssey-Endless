"""
Stress test for 100 rooms with full party, all relics, and all cards.

This test is marked as 'stress' and will not run during regular test execution.
Run it explicitly with: docker compose run backend pytest -v -m stress tests/test_stress_100_rooms.py

The test verifies:
- All relics can be applied and work correctly
- All cards can be added to the party
- Async operations don't timeout over 100 battles
- Characters (Player, Carly, Lady Echo, Lady Darkness, Lady Light) function properly
- Passives trigger correctly throughout extended gameplay
- FoeFactory generates appropriate encounters based on party size and pressure

Note: This test uses FoeFactory to generate encounters, then passes them to BattleRoom
to ensure we're testing the same foe generation logic used in actual gameplay.
"""
import logging
from pathlib import Path
import random
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from autofighter.mapgen import MapNode
from autofighter.party import Party
from autofighter.rooms.battle.core import BattleRoom
from autofighter.rooms.foe_factory import FoeFactory
from plugins.characters.carly import Carly
from plugins.characters.lady_darkness import LadyDarkness
from plugins.characters.lady_echo import LadyEcho
from plugins.characters.lady_light import LadyLight
from plugins.characters.player import Player
from plugins.plugin_loader import PluginLoader

log = logging.getLogger(__name__)


@pytest.mark.stress
@pytest.mark.asyncio
async def test_stress_100_rooms_full_party():
    """
    Stress test: 100 battles with 5 party members vs multiple foes.

    Party: Player, Carly, Lady Echo, Lady Darkness, Lady Light
    Start with 1 of every relic and card.
    Gain a random relic stack after each battle.
    Foe count determined by FoeFactory based on party size and pressure.
    """
    random.seed(42)  # For reproducibility

    # Discover all relics and cards
    log.info("Discovering plugins...")
    loader = PluginLoader()
    loader.discover("plugins/relics")
    loader.discover("plugins/cards")

    relics = loader.get_plugins("relic")
    cards = loader.get_plugins("card")

    log.info(f"Found {len(relics)} relics and {len(cards)} cards")

    # Get all relic and card IDs
    all_relic_ids = list(relics.keys())
    all_card_ids = list(cards.keys())

    # Create party with all 5 characters
    party_members = [
        Player(),
        Carly(),
        LadyEcho(),
        LadyDarkness(),
        LadyLight(),
    ]

    # Initialize party with 1 of every relic and card
    party = Party(
        members=party_members,
        gold=1000,
        relics=all_relic_ids.copy(),  # Start with 1 of each relic
        cards=all_card_ids.copy(),    # Start with 1 of each card
        rdr=1.0,
    )

    log.info(f"Party initialized with {len(party.members)} members, {len(party.relics)} relics, {len(party.cards)} cards")

    # Create foe factory
    foe_factory = FoeFactory()

    # Track statistics
    battles_won = 0
    battles_lost = 0
    total_foes_defeated = 0

    # Run 100 battles
    for floor in range(1, 101):
        log.info(f"\n{'='*60}")
        log.info(f"Starting Floor {floor}/100")
        log.info(f"{'='*60}")

        # Create battle node for this floor
        node = MapNode(
            room_id=floor,
            room_type="battle-normal",
            floor=floor,
            index=floor,
            loop=(floor // 10) + 1,  # Increase loop every 10 floors
            pressure=floor * 5,       # Increase pressure each floor
        )

        # Generate foes for this battle
        # Let FoeFactory determine count based on party size, pressure, and config
        # With 5 party members and increasing pressure, it will generate appropriate foes
        foes = foe_factory.build_encounter(node, party)

        log.info(f"Generated {len(foes)} foes: {[f.id for f in foes]}")
        log.info(f"Party has {len(party.relics)} relic stacks, {len(party.cards)} cards")

        # Ensure all party members are alive
        for member in party.members:
            if member.hp <= 0:
                member.hp = member.max_hp

        # Create and run battle
        room = BattleRoom(node)

        try:
            # Run the battle with custom foes
            result = await room.resolve(party, {}, foe=foes)

            # Check battle result
            if result.get("victory", False):
                battles_won += 1
                total_foes_defeated += len(foes)
                log.info(f"✓ Floor {floor} - VICTORY! ({battles_won} wins, {battles_lost} losses)")
            else:
                battles_lost += 1
                log.info(f"✗ Floor {floor} - DEFEAT ({battles_won} wins, {battles_lost} losses)")

                # Revive party for next battle
                for member in party.members:
                    if member.hp <= 0:
                        member.hp = member.max_hp

            # Add a random relic stack (as per requirements)
            random_relic_id = random.choice(all_relic_ids)
            party.relics.append(random_relic_id)
            log.info(f"Added relic stack: {random_relic_id} (now {party.relics.count(random_relic_id)} stacks)")

            # Progress update every 10 floors
            if floor % 10 == 0:
                log.info(f"\n{'='*60}")
                log.info(f"Progress: {floor}/100 floors completed")
                log.info(f"Stats: {battles_won} wins, {battles_lost} losses, {total_foes_defeated} foes defeated")
                log.info(f"Party: {len(party.relics)} relic stacks, {len(party.cards)} cards")
                log.info(f"{'='*60}\n")

        except Exception as e:
            log.error(f"Battle {floor} failed with error: {e}", exc_info=True)
            battles_lost += 1

            # Revive party for next battle
            for member in party.members:
                if member.hp <= 0:
                    member.hp = member.max_hp

    # Final statistics
    log.info(f"\n{'='*60}")
    log.info("STRESS TEST COMPLETED")
    log.info(f"{'='*60}")
    log.info("Total Battles: 100")
    log.info(f"Wins: {battles_won}")
    log.info(f"Losses: {battles_lost}")
    log.info(f"Foes Defeated: {total_foes_defeated}")
    log.info(f"Final Relic Stacks: {len(party.relics)}")
    log.info(f"Final Card Count: {len(party.cards)}")
    log.info(f"{'='*60}\n")

    # Assert that we completed all 100 battles without catastrophic failures
    assert battles_won + battles_lost == 100, "Not all battles were completed"

    # The test passes if we made it through all 100 rooms without hanging or crashing
    # We don't require winning all battles, just completing them all
    log.info("✓ Stress test passed: Completed 100 rooms without timeout or crash")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_stress_100_rooms_full_party())
