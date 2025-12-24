"""
Simplified shop system for idle game.
Adapted from backend/autofighter/rooms/shop.py.
"""

from __future__ import annotations

import math
import random
from typing import Any


# Base prices by rarity (stars)
PRICE_BY_STARS = {
    1: 20,
    2: 50,
    3: 100,
    4: 200,
    5: 500,
}

REROLL_COST = 10


def calculate_shop_price(
    base_price: int,
    pressure: int = 0,
    items_bought: int = 0,
    variance: tuple[float, float] = (0.95, 1.05),
) -> int:
    """Calculate shop price with pressure scaling and tax.
    
    Args:
        base_price: Base price of item
        pressure: Difficulty pressure (increases prices)
        items_bought: Number of items already bought (increases tax)
        variance: Price variance range for randomization
        
    Returns:
        Final price including tax and variance
    """
    # Apply pressure multiplier
    multiplier = 1.26 ** max(pressure, 0)
    
    # Apply price variance
    if variance[1] > variance[0]:
        multiplier *= random.uniform(variance[0], variance[1])
    
    # Calculate base price with pressure
    scaled_price = int(base_price * multiplier)
    
    # Calculate and add tax based on items bought
    if items_bought > 0:
        tax_rate = 0.01 * (max(pressure, 0) + 1) * items_bought
        tax = int(math.ceil(scaled_price * tax_rate))
        scaled_price += tax
    
    return scaled_price


def generate_shop_stock(
    gold: int,
    floor: int = 1,
    pressure: int = 0,
    items_bought: int = 0,
) -> list[dict[str, Any]]:
    """Generate shop stock based on current game state.
    
    Args:
        gold: Player's current gold
        floor: Current floor number
        pressure: Difficulty pressure
        items_bought: Number of items already bought
        
    Returns:
        List of shop items with prices
    """
    stock: list[dict[str, Any]] = []
    
    # Determine rarity distribution based on floor
    rarity_weights = {
        1: 50,  # Common
        2: 30,  # Uncommon
        3: 15,  # Rare
        4: 4,   # Epic
        5: 1,   # Legendary
    }
    
    # Improve weights on higher floors
    if floor >= 5:
        rarity_weights[3] += 5
        rarity_weights[4] += 2
    if floor >= 10:
        rarity_weights[4] += 3
        rarity_weights[5] += 2
    
    # Generate 4-6 items
    item_count = random.randint(4, 6)
    
    for _ in range(item_count):
        # Choose rarity
        rarities = list(rarity_weights.keys())
        weights = list(rarity_weights.values())
        rarity = random.choices(rarities, weights=weights)[0]
        
        # Base price for rarity
        base_price = PRICE_BY_STARS[rarity]
        
        # Calculate final price
        final_price = calculate_shop_price(
            base_price,
            pressure=pressure,
            items_bought=items_bought,
        )
        
        # Create item entry
        item = {
            "type": random.choice(["card", "relic", "passive"]),
            "rarity": rarity,
            "base_price": base_price,
            "price": final_price,
            "affordable": gold >= final_price,
        }
        
        stock.append(item)
    
    # Sort by price
    stock.sort(key=lambda x: x["price"])
    
    return stock


def apply_purchase(
    stock: list[dict[str, Any]],
    item_index: int,
    gold: int,
) -> tuple[list[dict[str, Any]], int, dict[str, Any] | None]:
    """Apply a purchase to the shop stock.
    
    Args:
        stock: Current shop stock
        item_index: Index of item to purchase
        gold: Player's current gold
        
    Returns:
        Tuple of (updated_stock, remaining_gold, purchased_item)
    """
    if item_index < 0 or item_index >= len(stock):
        return stock, gold, None
    
    item = stock[item_index]
    price = item["price"]
    
    if gold < price:
        return stock, gold, None
    
    # Remove item from stock
    updated_stock = stock[:item_index] + stock[item_index + 1:]
    
    # Deduct gold
    remaining_gold = gold - price
    
    return updated_stock, remaining_gold, item


def apply_reroll(
    gold: int,
    floor: int = 1,
    pressure: int = 0,
    items_bought: int = 0,
) -> tuple[list[dict[str, Any]], int]:
    """Reroll shop stock.
    
    Args:
        gold: Player's current gold
        floor: Current floor number
        pressure: Difficulty pressure
        items_bought: Number of items already bought
        
    Returns:
        Tuple of (new_stock, remaining_gold)
    """
    if gold < REROLL_COST:
        return [], gold
    
    new_stock = generate_shop_stock(
        gold - REROLL_COST,
        floor=floor,
        pressure=pressure,
        items_bought=items_bought,
    )
    
    return new_stock, gold - REROLL_COST
