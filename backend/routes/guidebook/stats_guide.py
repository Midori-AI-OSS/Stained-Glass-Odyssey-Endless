"""Stats reference endpoint."""

from __future__ import annotations

from typing import Any

from quart import jsonify

from . import bp


@bp.get("/stats")
async def stats() -> tuple[str, int, dict[str, Any]]:
    """Detailed breakdown of all character stats and their effects."""
    stats_info = [
        {
            "name": "Health Points (HP)",
            "description": "Your current health. When it reaches 0, you're defeated. Can be healed through various means.",
            "base_value": "1000",
            "scaling": "+10 per level"
        },
        {
            "name": "Attack (ATK)",
            "description": "Determines damage dealt to enemies. Higher attack means stronger abilities and ultimates.",
            "base_value": "200",
            "scaling": "+5 per level"
        },
        {
            "name": "Defense (DEF)",
            "description": "Reduces incoming damage. Higher defense makes you more resilient to enemy attacks.",
            "base_value": "200",
            "scaling": "+3 per level"
        },
        {
            "name": "Critical Rate",
            "description": "Chance to deal critical hits for increased damage. Default critical damage is 2x normal damage.",
            "base_value": "5%",
            "scaling": "Affected by cards and relics"
        },
        {
            "name": "Critical Damage",
            "description": "Multiplier for critical hit damage. Works with critical rate to boost damage output.",
            "base_value": "200%",
            "scaling": "Affected by cards and relics"
        },
        {
            "name": "Vitality",
            "description": "Affects healing, damage, damage reduction, and experience gain.",
            "base_value": "1.0x",
            "scaling": "Affected by cards and relics"
        },
        {
            "name": "Effect Hit Rate",
            "description": "Chance for your damage-over-time effects and debuffs to successfully apply to enemies.",
            "base_value": "100%",
            "scaling": "Affected by cards and relics"
        },
        {
            "name": "Effect Resistance",
            "description": "Reduces the chance of enemy effects (DoTs, debuffs) successfully affecting you.",
            "base_value": "5%",
            "scaling": "Affected by cards and relics"
        },
        {
            "name": "Dodge Rate",
            "description": "Chance to completely avoid incoming attacks, taking no damage.",
            "base_value": "5%",
            "scaling": "Affected by cards and relics"
        },
        {
            "name": "Mitigation",
            "description": "Additional damage reduction multiplier applied after defense calculations.",
            "base_value": "1.0x",
            "scaling": "Affected by cards and relics"
        }
    ]

    # Add passive explanations
    common_passives = [
        {
            "name": "Room Heal",
            "description": "Heal for 1 HP at the end of each battle. Stacks provide additional healing.",
            "trigger": "After battle"
        },
        {
            "name": "Attack Up",
            "description": "Gain +5 attack at the start of each battle. Stacks provide additional attack.",
            "trigger": "Before battle"
        }
    ]

    return jsonify({
        "stats": stats_info,
        "common_passives": common_passives,
        "level_info": {
            "description": "Multiple level systems provide character progression.",
            "in_run_leveling": "Characters gain EXP in runs and level up for fixed stat gains (+10 HP, +5 ATK, +3 DEF) plus 0.3%-0.8% boost to ALL stats",
            "global_user_level": "Persistent level across runs that provides permanent stat scaling to all characters",
            "experience": "Gain XP by winning battles and completing runs. Vitality multiplies EXP gain."
        }
    }), 200
