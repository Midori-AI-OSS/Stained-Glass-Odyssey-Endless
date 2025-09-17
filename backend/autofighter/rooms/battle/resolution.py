"""Reward resolution helpers for battle victories."""

from __future__ import annotations

import logging
import random
from typing import TYPE_CHECKING
from typing import Any
from typing import Sequence

from autofighter.cards import card_choices
from autofighter.relics import relic_choices
from autofighter.stats import BUS
from autofighter.summons.base import Summon
from plugins.damage_types import ALL_DAMAGE_TYPES
from plugins.relics.fallback_essence import FallbackEssence

from ...party import Party
from .rewards import _apply_rdr_to_stars
from .rewards import _calc_gold
from .rewards import _pick_card_stars
from .rewards import _pick_item_stars
from .rewards import _pick_relic_stars
from .rewards import _roll_relic_drop

if TYPE_CHECKING:
    from battle_logging.writers import BattleLogger

    from .core import BattleRoom


log = logging.getLogger(__name__)


ELEMENTS = [element.lower() for element in ALL_DAMAGE_TYPES]


async def resolve_rewards(
    *,
    room: BattleRoom,
    party: Party,
    combat_party: Party,
    foes: Sequence[Any],
    foes_data: list[dict[str, Any]],
    enrage_payload: dict[str, Any],
    start_gold: int,
    temp_rdr: float,
    party_data: list[dict[str, Any]],
    party_summons: dict[str, Any],
    foe_summons: dict[str, Any],
    action_queue_snapshot: dict[str, Any],
    battle_logger: BattleLogger | None,
    exp_reward: int,
) -> dict[str, Any]:
    """Assemble the battle victory payload including loot and choices."""

    selected_cards: list[Any] = []
    attempts = 0
    log.info(
        "Starting card selection for run %s, party has %d cards",
        getattr(combat_party, "cards", []),
        len(getattr(combat_party, "cards", [])),
    )
    while len(selected_cards) < 3 and attempts < 30:
        attempts += 1
        base_stars = _pick_card_stars(room)
        card_stars = _apply_rdr_to_stars(base_stars, temp_rdr)
        log.debug(
            "Card selection attempt %d: base_stars=%d, rdr_stars=%d",
            attempts,
            base_stars,
            card_stars,
        )
        choices = card_choices(combat_party, card_stars, count=1)
        log.debug("  card_choices returned %d options", len(choices))
        if not choices:
            log.debug("  No cards available for star level %d", card_stars)
            continue
        candidate = choices[0]
        log.debug(
            "  Candidate card: %s (%s) - %d stars",
            candidate.id,
            candidate.name,
            candidate.stars,
        )
        if any(card.id == candidate.id for card in selected_cards):
            log.debug("  Card %s already selected, skipping", candidate.id)
            continue
        selected_cards.append(candidate)
        log.debug("  Added card: %s", candidate.id)
    log.info(
        "Card selection complete: %d cards selected after %d attempts",
        len(selected_cards),
        attempts,
    )
    if selected_cards:
        log.info("Selected cards: %s", [card.id for card in selected_cards])
    else:
        log.warning("No cards were selected!")
    card_choice_data = [
        {
            "id": card.id,
            "name": card.name,
            "stars": card.stars,
            "about": card.about,
        }
        for card in selected_cards
    ]

    relic_options: list[Any] = []
    if _roll_relic_drop(room, temp_rdr):
        picked: list[Any] = []
        tries = 0
        while len(picked) < 3 and tries < 30:
            tries += 1
            relic_stars = _apply_rdr_to_stars(
                _pick_relic_stars(room),
                temp_rdr,
            )
            choices = relic_choices(combat_party, relic_stars, count=1)
            if not choices:
                continue
            relic = choices[0]
            if any(existing.id == relic.id for existing in picked):
                continue
            picked.append(relic)
        relic_options = picked

    if not selected_cards:
        fallback_relic = FallbackEssence()
        if not relic_options:
            relic_options = [fallback_relic]
        else:
            relic_options.append(fallback_relic)

    relic_choice_data = [
        {
            "id": relic.id,
            "name": relic.name,
            "stars": relic.stars,
            "about": relic.describe(party.relics.count(relic.id) + 1),
            "stacks": party.relics.count(relic.id),
        }
        for relic in relic_options
    ]

    gold_reward = _calc_gold(room, temp_rdr)
    party.gold += gold_reward
    await BUS.emit_async("gold_earned", gold_reward)

    item_base = 1 * temp_rdr
    base_int = int(item_base)
    item_count = max(1, base_int)
    if random.random() < item_base - base_int:
        item_count += 1
    items = [
        {"id": random.choice(ELEMENTS), "stars": _pick_item_stars(room)}
        for _ in range(item_count)
    ]
    node = getattr(room, "node", None)
    is_floor_boss = getattr(node, "room_type", "") == "battle-boss-floor"
    is_boss_strength = getattr(room, "strength", 1.0) > 1.0
    ticket_drop = False
    if is_floor_boss:
        ticket_drop = True
    else:
        ticket_chance = 0.0005 * temp_rdr
        if is_boss_strength:
            boosted = min(0.05 * temp_rdr, 1.0)
            ticket_chance = max(ticket_chance, boosted)
        if random.random() < ticket_chance:
            ticket_drop = True
    if ticket_drop:
        items.append({"id": "ticket", "stars": 0})

    loot = {
        "gold": party.gold - start_gold,
        "card_choices": card_choice_data,
        "relic_choices": relic_choice_data,
        "items": items,
    }
    log.info(
        "Battle rewards: gold=%s cards=%s relics=%s items=%s",
        loot["gold"],
        [choice["id"] for choice in card_choice_data],
        [choice["id"] for choice in relic_choice_data],
        items,
    )

    return {
        "result": "boss" if room.strength > 1.0 else "battle",
        "party": party_data,
        "party_summons": party_summons,
        "gold": party.gold,
        "relics": party.relics,
        "cards": party.cards,
        "card_choices": card_choice_data,
        "relic_choices": relic_choice_data,
        "loot": loot,
        "foes": [
            foe_info
            for foe_obj, foe_info in zip(foes, foes_data, strict=False)
            if not isinstance(foe_obj, Summon)
        ],
        "foe_summons": foe_summons,
        "room_number": room.node.index,
        "battle_index": getattr(battle_logger, "battle_index", 0) if battle_logger else 0,
        "exp_reward": exp_reward,
        "enrage": enrage_payload,
        "rdr": party.rdr,
        "action_queue": action_queue_snapshot,
        "ended": True,
    }
