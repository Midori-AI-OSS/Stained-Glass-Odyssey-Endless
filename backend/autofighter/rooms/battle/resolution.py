"""Reward resolution helpers for battle victories."""

from __future__ import annotations

from collections.abc import Mapping
import logging
import math
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
from . import snapshots as _snapshots
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


def _pick_weighted_element(
    drop_weights: Mapping[str, float] | None,
) -> str:
    weights = {element: 1.0 for element in ELEMENTS}
    if isinstance(drop_weights, Mapping):
        for key, value in drop_weights.items():
            try:
                bonus = float(value)
            except (TypeError, ValueError):
                continue
            if bonus <= 0:
                continue
            lowered = str(key or "").lower()
            if lowered == "all" or not lowered:
                for element in weights:
                    weights[element] += bonus
            elif lowered in weights:
                weights[lowered] += bonus
    total = sum(weight for weight in weights.values() if weight > 0)
    if total <= 0:
        return random.choice(ELEMENTS)
    pick = random.random() * total
    cumulative = 0.0
    for element, weight in weights.items():
        if weight <= 0:
            continue
        cumulative += weight
        if pick <= cumulative:
            return element
    return ELEMENTS[-1]


def _generate_item_rewards(
    room: BattleRoom,
    temp_rdr: float,
    drop_weights: Mapping[str, float] | None = None,
) -> list[dict[str, Any]]:
    """Create item rewards using bounded upgrades for very high rdr."""

    multiplier = max(temp_rdr, 1.0)
    baseline_stars = _pick_item_stars(room)

    log_multiplier = math.log10(multiplier)
    sequential_upgrades = int(log_multiplier)

    stars = baseline_stars
    applied_upgrades = 0
    while applied_upgrades < sequential_upgrades and stars < 4:
        stars += 1
        applied_upgrades += 1
    stars = min(stars, 4)

    residual_multiplier = multiplier / (10 ** applied_upgrades)
    capped_residual = min(residual_multiplier, 10.0)
    extra_drop_chance = max(0.0, min((capped_residual - 1.0) / 9.0, 1.0))

    element = _pick_weighted_element(drop_weights)
    items = [{"id": element, "stars": stars}]

    if random.random() < extra_drop_chance:
        consolation_stars = min(baseline_stars, stars)
        items.append({"id": element, "stars": consolation_stars})

    return items


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
    run_id: str | None,
    effects_charge: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assemble the battle victory payload including loot and choices."""

    card_options: list[Any] = []
    log.info(
        "Generating card reward options for run %s, party has %d cards",
        getattr(combat_party, "cards", []),
        len(getattr(combat_party, "cards", [])),
    )
    base_stars = _pick_card_stars(room)
    target_stars = _apply_rdr_to_stars(base_stars, temp_rdr)
    star_buckets = [
        stars for stars in range(target_stars, 0, -1) if stars > 0
    ]
    seen_ids: set[str] = set()
    for stars in star_buckets:
        if len(card_options) >= 3:
            break
        remaining = 3 - len(card_options)
        choices = card_choices(combat_party, stars, count=remaining)
        log.debug(
            "Card option pass: stars=%d, requested=%d, received=%d",
            stars,
            remaining,
            len(choices),
        )
        for candidate in choices:
            if candidate.id in seen_ids:
                continue
            seen_ids.add(candidate.id)
            card_options.append(candidate)
            if len(card_options) >= 3:
                break
    log.info(
        "Card reward options generated: %d choices (target_stars=%d)",
        len(card_options),
        target_stars,
    )
    if not card_options:
        log.warning("No card reward options available")
    card_choice_data = [
        {
            "id": card.id,
            "name": card.name,
            "stars": card.stars,
            "about": card.about,
        }
        for card in card_options
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

    if not card_options:
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
            "about": relic.get_about_str(stacks=party.relics.count(relic.id) + 1),
            "stacks": party.relics.count(relic.id),
        }
        for relic in relic_options
    ]

    gold_reward = _calc_gold(room, temp_rdr)
    party.gold += gold_reward
    await BUS.emit_async("gold_earned", gold_reward)

    drop_weights = getattr(party, "login_theme_drop_weights", None)
    items = _generate_item_rewards(room, temp_rdr, drop_weights)
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

    result = {
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
    charges: list[dict[str, Any]] | None = None
    if run_id:
        charges = _snapshots.get_effect_charges(run_id)
    if charges is None:
        charges = effects_charge
    if charges:
        result["effects_charge"] = charges
    return result
