"""
Simplified foe factory for creating enemies.
Adapted from backend/autofighter/rooms/foe_factory.py.
"""

from __future__ import annotations

import random
from typing import Any


def create_foe(
    foe_id: str,
    floor: int = 1,
    difficulty: str = "normal",
    pressure: int = 0,
) -> dict[str, Any]:
    """Create a foe with scaled stats.
    
    Args:
        foe_id: Identifier for the foe type
        floor: Current floor number
        difficulty: Difficulty level (weak, normal, elite, prime, boss)
        pressure: Additional difficulty pressure
        
    Returns:
        Dictionary with foe data
    """
    # Base stats
    base_hp = 100
    base_atk = 10
    base_def = 5

    # Scale by floor
    floor_multiplier = 1.0 + (floor - 1) * 0.15

    # Scale by difficulty
    difficulty_multipliers = {
        "weak": 0.7,
        "normal": 1.0,
        "elite": 1.5,
        "prime": 2.0,
        "boss": 3.0,
    }
    diff_mult = difficulty_multipliers.get(difficulty, 1.0)

    # Scale by pressure
    pressure_mult = 1.0 + (pressure * 0.1)

    # Calculate final stats
    total_mult = floor_multiplier * diff_mult * pressure_mult

    foe = {
        "id": foe_id,
        "name": foe_id.replace("_", " ").title(),
        "hp": int(base_hp * total_mult),
        "max_hp": int(base_hp * total_mult),
        "atk": int(base_atk * total_mult),
        "def": int(base_def * total_mult),
        "floor": floor,
        "difficulty": difficulty,
        "pressure": pressure,
        "is_boss": difficulty == "boss",
        "is_elite": difficulty in ("elite", "prime", "boss"),
    }

    return foe


def generate_enemy_party(
    floor: int = 1,
    difficulty: str = "normal",
    pressure: int = 0,
    enemy_count: int | None = None,
) -> list[dict[str, Any]]:
    """Generate a party of enemies for a battle.
    
    Args:
        floor: Current floor number
        difficulty: Difficulty level
        pressure: Additional difficulty pressure
        enemy_count: Optional fixed enemy count (otherwise determined by difficulty)
        
    Returns:
        List of enemy dictionaries
    """
    # Determine enemy count if not specified
    if enemy_count is None:
        if difficulty == "boss":
            enemy_count = 1
        elif difficulty in ("elite", "prime"):
            enemy_count = random.randint(1, 2)
        elif difficulty == "normal":
            enemy_count = random.randint(2, 3)
        else:  # weak
            enemy_count = random.randint(1, 2)

    # Pool of enemy types
    enemy_types = [
        "slime",
        "goblin",
        "skeleton",
        "wolf",
        "bandit",
        "spider",
        "orc",
        "troll",
        "demon",
        "dragon",
    ]

    # Select appropriate enemies based on floor
    if floor <= 3:
        available = enemy_types[:4]
    elif floor <= 6:
        available = enemy_types[:6]
    elif floor <= 10:
        available = enemy_types[:8]
    else:
        available = enemy_types

    # Generate enemies
    enemies: list[dict[str, Any]] = []

    for i in range(enemy_count):
        enemy_type = random.choice(available)
        foe_id = f"{enemy_type}_{floor}_{i}"

        enemy = create_foe(
            foe_id=foe_id,
            floor=floor,
            difficulty=difficulty,
            pressure=pressure,
        )

        enemies.append(enemy)

    return enemies
