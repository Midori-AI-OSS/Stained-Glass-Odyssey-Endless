"""Reward resolution helpers for battle victories.

Ported from backend/autofighter/rooms/battle/resolution.py
Simplified for Qt-based idle game (synchronous, no web logging).
"""

import math
import random
from typing import Any

# Base reward constants
BASE_GOLD_MIN = 10
BASE_GOLD_MAX = 50
BASE_EXP_MIN = 20
BASE_EXP_MAX = 100

# Star rating probabilities (0-4 stars)
CARD_STAR_WEIGHTS = [0.4, 0.3, 0.2, 0.08, 0.02]  # 0-4 stars
RELIC_STAR_WEIGHTS = [0.5, 0.3, 0.15, 0.04, 0.01]  # 0-4 stars
ITEM_STAR_WEIGHTS = [0.45, 0.35, 0.15, 0.04, 0.01]  # 0-4 stars


def calculate_battle_rewards(
    context: Any,
    victory: bool = True,
    temp_rdr: float = 1.0,
) -> dict[str, Any]:
    """Calculate all battle rewards (gold, exp, cards, relics, items).

    Args:
        context: TurnLoopContext with battle state
        victory: Whether the party won
        temp_rdr: Temporary rare drop rate multiplier

    Returns:
        Dictionary with reward data
    """
    if not victory:
        # Defeat rewards (minimal)
        return {
            "victory": False,
            "gold": 0,
            "exp": 0,
            "cards": [],
            "relics": [],
            "items": [],
        }

    # Calculate base rewards
    gold = _calculate_gold(context, temp_rdr)
    exp = _calculate_exp(context)

    # Generate drops
    cards = _generate_card_rewards(context, temp_rdr)
    relics = _generate_relic_rewards(context, temp_rdr)
    items = _generate_item_rewards(context, temp_rdr)

    return {
        "victory": True,
        "gold": gold,
        "exp": exp,
        "cards": cards,
        "relics": relics,
        "items": items,
    }


def _calculate_gold(context: Any, temp_rdr: float = 1.0) -> int:
    """Calculate gold reward based on battle difficulty.

    Args:
        context: Battle context with foe data
        temp_rdr: Rare drop rate multiplier

    Returns:
        Gold amount
    """
    # Base gold from foe count and levels
    foe_count = len(context.foes)
    avg_foe_level = sum(getattr(f, "level", 1) for f in context.foes) / max(foe_count, 1)

    base_gold = random.randint(BASE_GOLD_MIN, BASE_GOLD_MAX)
    level_bonus = int(avg_foe_level * 5)
    count_bonus = int((foe_count - 1) * 10)

    total_gold = base_gold + level_bonus + count_bonus

    # Apply RDR multiplier
    multiplier = max(temp_rdr, 1.0)
    total_gold = int(total_gold * multiplier)

    return max(total_gold, 1)


def _calculate_exp(context: Any) -> int:
    """Calculate experience reward based on battle difficulty.

    Args:
        context: Battle context with foe and party data

    Returns:
        Experience points
    """
    # Base exp from foe count and levels
    foe_count = len(context.foes)
    total_foe_levels = sum(getattr(f, "level", 1) for f in context.foes)

    base_exp = random.randint(BASE_EXP_MIN, BASE_EXP_MAX)
    level_exp = total_foe_levels * 10
    count_bonus = int((foe_count - 1) * 15)

    total_exp = base_exp + level_exp + count_bonus

    # Add turn efficiency bonus (shorter battles = more exp)
    turn_count = context.turn
    if turn_count < 10:
        total_exp = int(total_exp * 1.2)
    elif turn_count < 20:
        total_exp = int(total_exp * 1.1)

    return max(total_exp, 1)


def _generate_card_rewards(context: Any, temp_rdr: float = 1.0) -> list[dict[str, Any]]:
    """Generate card rewards based on RDR.

    Args:
        context: Battle context
        temp_rdr: Rare drop rate multiplier

    Returns:
        List of card reward dicts
    """
    cards = []

    # Base drop chance
    drop_chance = 0.3  # 30% base chance
    drop_chance = min(drop_chance * temp_rdr, 0.95)

    if random.random() < drop_chance:
        # Pick star rating
        stars = _pick_weighted_stars(CARD_STAR_WEIGHTS, temp_rdr)

        # Pick element (simplified - random for now)
        elements = ["Fire", "Ice", "Lightning", "Wind", "Light", "Dark", "Generic"]
        element = random.choice(elements)

        cards.append(
            {
                "type": "card",
                "element": element,
                "stars": stars,
                "id": f"{element.lower()}_card_{stars}star",
            }
        )

    return cards


def _generate_relic_rewards(context: Any, temp_rdr: float = 1.0) -> list[dict[str, Any]]:
    """Generate relic rewards based on RDR.

    Args:
        context: Battle context
        temp_rdr: Rare drop rate multiplier

    Returns:
        List of relic reward dicts
    """
    relics = []

    # Base drop chance (lower than cards)
    drop_chance = 0.15  # 15% base chance
    drop_chance = min(drop_chance * temp_rdr, 0.75)

    if random.random() < drop_chance:
        # Pick star rating
        stars = _pick_weighted_stars(RELIC_STAR_WEIGHTS, temp_rdr)

        relics.append(
            {
                "type": "relic",
                "stars": stars,
                "id": f"relic_{stars}star",
            }
        )

    return relics


def _generate_item_rewards(context: Any, temp_rdr: float = 1.0) -> list[dict[str, Any]]:
    """Generate item/essence rewards based on RDR.

    Args:
        context: Battle context
        temp_rdr: Rare drop rate multiplier

    Returns:
        List of item reward dicts
    """
    items = []

    # Items drop more frequently
    drop_chance = 0.5  # 50% base chance
    drop_chance = min(drop_chance * temp_rdr, 0.98)

    if random.random() < drop_chance:
        # Pick star rating
        stars = _pick_weighted_stars(ITEM_STAR_WEIGHTS, temp_rdr)

        # Pick element
        elements = ["Fire", "Ice", "Lightning", "Wind", "Light", "Dark"]
        element = random.choice(elements)

        items.append(
            {
                "type": "essence",
                "element": element,
                "stars": stars,
                "id": f"{element.lower()}_essence",
            }
        )

    # High RDR can give bonus items
    if temp_rdr > 5.0 and random.random() < 0.3:
        stars = _pick_weighted_stars(ITEM_STAR_WEIGHTS, temp_rdr)
        element = random.choice(elements)
        items.append(
            {
                "type": "essence",
                "element": element,
                "stars": stars,
                "id": f"{element.lower()}_essence",
            }
        )

    return items


def _pick_weighted_stars(weights: list[float], rdr_multiplier: float = 1.0) -> int:
    """Pick star rating using weighted probabilities with RDR boost.

    Args:
        weights: List of probabilities for 0-4 stars
        rdr_multiplier: Multiplier to boost higher star chances

    Returns:
        Star rating (0-4)
    """
    # Apply RDR multiplier to shift probabilities toward higher stars
    # Use logarithmic scaling to avoid making high stars too common
    if rdr_multiplier > 1.0:
        log_multiplier = math.log10(rdr_multiplier)
        # Shift probability mass upward
        adjusted_weights = []
        for i, weight in enumerate(weights):
            # Higher stars get bigger boost
            boost = 1.0 + (log_multiplier * (i / len(weights)))
            adjusted_weights.append(weight * boost)
        weights = adjusted_weights

    # Normalize weights
    total = sum(weights)
    if total <= 0:
        return 0

    # Pick randomly
    pick = random.random() * total
    cumulative = 0.0
    for stars, weight in enumerate(weights):
        cumulative += weight
        if pick <= cumulative:
            return stars

    return len(weights) - 1  # Return max stars as fallback
