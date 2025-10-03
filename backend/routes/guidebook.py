from __future__ import annotations

from importlib import import_module
from typing import Any

from quart import Blueprint
from quart import jsonify

from autofighter.passives import discover as discover_passives
from autofighter.rooms.shop import PRICE_BY_STARS
from autofighter.rooms.shop import REROLL_COST
from plugins.damage_types import ALL_DAMAGE_TYPES
from plugins.damage_types import load_damage_type
from tracking import log_menu_action
from tracking import log_overlay_action

bp = Blueprint("guidebook", __name__, url_prefix="/guidebook")


def _load_damage_type_class(name: str):
    try:
        module = import_module(f"plugins.damage_types.{name.lower()}")
        return getattr(module, name)
    except Exception:
        module = import_module("plugins.damage_types.generic")
        return module.Generic


def _compute_strong_against_map() -> dict[str, list[str]]:
    all_types = list(ALL_DAMAGE_TYPES)
    weakness_by_type: dict[str, str] = {}

    for name in all_types:
        cls = _load_damage_type_class(name)
        weakness = getattr(cls, "weakness", None)
        if isinstance(weakness, str) and weakness.lower() != "none":
            weakness_by_type[name] = weakness

    strong_map: dict[str, list[str]] = {}
    for type_name, weakness in weakness_by_type.items():
        strong_map.setdefault(weakness, []).append(type_name)

    for attacker in strong_map:
        strong_map[attacker].sort()

    return strong_map


def _elemental_resistance_summary() -> str:
    strong_map = _compute_strong_against_map()

    primary_order = ["Fire", "Ice", "Lightning", "Wind"]
    relationships: list[str] = []

    for attacker in primary_order:
        for target in strong_map.get(attacker, []):
            relationships.append(f"{attacker}→{target}")

    light_targets = set(strong_map.get("Light", []))
    dark_targets = set(strong_map.get("Dark", []))
    if "Dark" in light_targets and "Light" in dark_targets:
        relationships.append("Light↔Dark")
    else:
        for target in sorted(light_targets):
            relationships.append(f"Light→{target}")
        for target in sorted(dark_targets):
            relationships.append(f"Dark→{target}")

    handled = set(primary_order + ["Light", "Dark"])
    remaining = sorted(name for name in strong_map if name not in handled)
    for attacker in remaining:
        for target in strong_map[attacker]:
            relationships.append(f"{attacker}→{target}")

    return ", ".join(relationships)


@bp.get("/damage-types")
async def damage_types() -> tuple[str, int, dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    # Process all official types plus Generic
    all_types = list(ALL_DAMAGE_TYPES) + ["Generic"]
    for name in all_types:
        inst = load_damage_type(name)
        cls = type(inst)

        # Try to get description from the plugin itself
        desc = None
        if hasattr(cls, "get_description"):
            desc = cls.get_description()
        elif hasattr(cls, "__doc__") and cls.__doc__:
            desc = cls.__doc__.strip()

        # Fallback to analyzing the plugin's behavior
        if not desc:
            weakness = getattr(inst, "weakness", None)
            if weakness and weakness != "none":
                desc = f"Elemental damage type. Weak to {weakness}."
            else:
                desc = "Elemental damage type."

        # Calculate what this type is strong against
        strong_against = None
        for other_name in all_types:
            other_inst = load_damage_type(other_name)
            if getattr(other_inst, "weakness", None) == name:
                strong_against = other_name
                break

        entries.append(
            {
                "id": getattr(inst, "id", name),
                "weakness": getattr(inst, "weakness", None),
                "strong_against": strong_against,
                "color": getattr(inst, "color", None),
                "description": str(desc).strip(),
                "damage_mod_weak": "1.25x damage when attacking weakness",
                "damage_mod_resist": "0.75x damage when attacking same type"
            }
        )
    payload = {"damage_types": entries}
    try:
        await log_menu_action("Guidebook", "view_damage_types", {"count": len(entries)})
        await log_overlay_action("guidebook", {"section": "damage_types"})
    except Exception:
        pass
    return jsonify(payload), 200


@bp.get("/ultimates")
async def ultimates() -> tuple[str, int, dict[str, Any]]:
    info: list[dict[str, Any]] = []

    # Include Generic type in ultimates
    all_types = list(ALL_DAMAGE_TYPES) + ["Generic"]

    for name in all_types:
        inst = load_damage_type(name)
        cls = type(inst)

        # Try to extract docstring from ultimate implementation
        doc = None
        if hasattr(cls.ultimate, "__doc__") and cls.ultimate.__doc__:
            doc = cls.ultimate.__doc__.strip()
        elif hasattr(cls, "get_ultimate_description"):
            doc = cls.get_ultimate_description()
        elif hasattr(cls, "__doc__") and cls.__doc__:
            # Use class docstring if available
            doc = cls.__doc__.strip()

        # Fallback descriptions based on damage type if no docstring
        if not doc:
            doc = f"{name} ultimate ability."

        info.append({"id": getattr(inst, "id", name), "description": str(doc).strip()})
    payload = {"ultimates": info}
    try:
        await log_menu_action("Guidebook", "view_ultimates", {"count": len(info)})
        await log_overlay_action("guidebook", {"section": "ultimates"})
    except Exception:
        pass
    return jsonify(payload), 200


@bp.get("/passives")
async def passives() -> tuple[str, int, dict[str, Any]]:
    registry = discover_passives()
    items: list[dict[str, Any]] = []

    for pid, cls in sorted(registry.items()):
        name = getattr(cls, "name", pid)
        trigger = getattr(cls, "trigger", None)

        # Try to get description from the plugin itself
        desc = None
        if hasattr(cls, "get_description"):
            desc = cls.get_description()
        elif hasattr(cls, "__doc__") and cls.__doc__:
            desc = cls.__doc__.strip()

        # Fallback to creating description from metadata
        if not desc:
            # Create a basic description based on the passive metadata
            if trigger:
                desc = f"Passive ability that triggers on {trigger}."
            else:
                desc = f"Passive ability: {name}."

        # Get additional metadata if available
        amount = getattr(cls, "amount", None)
        stack_display = getattr(cls, "stack_display", None)

        effect_info = ""
        if amount is not None:
            effect_info += f" Base effect: {amount}"
        if stack_display:
            effect_info += f" (Stacks: {stack_display})"

        items.append(
            {
                "id": pid,
                "name": name,
                "trigger": trigger,
                "description": str(desc).strip() + effect_info,
                "amount": amount,
                "stack_display": stack_display
            }
        )
    payload = {"passives": items}
    try:
        await log_menu_action("Guidebook", "view_passives", {"count": len(items)})
        await log_overlay_action("guidebook", {"section": "passives"})
    except Exception:
        pass
    return jsonify(payload), 200


@bp.get("/shops")
async def shops() -> tuple[str, int, dict[str, Any]]:
    return jsonify({
        "reroll_cost": REROLL_COST,
        "price_by_stars": PRICE_BY_STARS,
        "notes": [
            "Shop stock includes cards and relics; prices scale with rarity (star rating).",
            "Reroll generates a new stock list at a fixed gold cost.",
            "Higher star items are more powerful but significantly more expensive.",
            "Stock quality and quantity may improve as you progress through runs."
        ],
        "pricing_explanation": {
            "1_star": f"{PRICE_BY_STARS.get(1, 10)} gold - Common items, basic effects",
            "2_star": f"{PRICE_BY_STARS.get(2, 25)} gold - Improved effects and utility",
            "3_star": f"{PRICE_BY_STARS.get(3, 50)} gold - Strong effects, good value",
            "4_star": f"{PRICE_BY_STARS.get(4, 100)} gold - Very powerful, rare items",
            "5_star": f"{PRICE_BY_STARS.get(5, 200)} gold - Extremely rare, game-changing",
            "6_star": f"{PRICE_BY_STARS.get(6, 500)} gold - Legendary items, run-defining"
        },
        "strategy_tips": [
            "Save gold early for high-star items that appear later",
            "Reroll when current stock doesn't fit your build",
            "4+ star items can dramatically change your strategy"
        ]
    }), 200


@bp.get("/ui")
async def ui() -> tuple[str, int, dict[str, Any]]:
    tips = [
        {"name": "Overlays", "description": "Open Settings, Inventory, and Guidebook from the main menu."},
        {"name": "Battle Review", "description": "After battles, view damage by type and proceed to the next room."},
        {"name": "Rewards", "description": "Choose cards, relics, and loot when available before advancing."},
    ]
    return jsonify({"tips": tips}), 200


@bp.get("/mechs")
async def mechs() -> tuple[str, int, dict[str, Any]]:
    mechanics = [
        {"name": "Ultimate Charge", "description": "Gain charge during combat; spend it to use your damage type's ultimate."},
        {"name": "DoTs & HoTs", "description": "Damage/Healing over time effects stack and interact with some elements."},
        {"name": "Enrage", "description": "Foes may gain enrage increasing difficulty as rooms progress."},
        {
            "name": "Elemental Resistances",
            "description": (
                "Each damage type has a weakness: "
                f"{_elemental_resistance_summary()}. Generic has no weaknesses."
            )
        },
        {"name": "Vitality Scaling", "description": "Affects healing, damage dealt, damage reduction, and experience gain."},
        {"name": "Level Benefits", "description": "In-run leveling grants fixed stats (+10 HP, +5 ATK, +3 DEF) plus 0.3%-0.8% boost to ALL stats per level. Global user level provides persistent stat scaling across runs."},
    ]
    return jsonify({"mechanics": mechanics}), 200


@bp.get("/effects")
async def effects() -> tuple[str, int, dict[str, Any]]:
    """Get information about combat effects, buffs, and DoTs."""

    # Load combat effects from plugins/effects/
    combat_effects = []
    try:
        from plugins.effects.aftertaste import Aftertaste
        combat_effects.append({
            "name": "Aftertaste",
            "type": "Combat Effect",
            "description": Aftertaste.get_description(),
            "trigger": "Various sources (relics, abilities) when hitting targets with damage"
        })
    except ImportError:
        pass

    try:
        from plugins.effects.critical_boost import CriticalBoost
        combat_effects.append({
            "name": "Critical Boost",
            "type": "Buff",
            "description": CriticalBoost.get_description(),
            "trigger": "Various sources"
        })
    except ImportError:
        pass

    # Load DoT effects from plugins/dots/
    import importlib
    import os
    dot_effects = []

    dots_dir = "plugins/dots"
    if os.path.exists(dots_dir):
        for filename in os.listdir(dots_dir):
            if filename.endswith(".py") and not filename.startswith("_") and filename != "__init__.py":
                module_name = filename[:-3]  # Remove .py extension
                try:
                    module = importlib.import_module(f"plugins.dots.{module_name}")
                    # Find the main class in the module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and
                            hasattr(attr, "plugin_type") and
                            attr.plugin_type == "dot" and
                            hasattr(attr, "id")):

                            # Get description from docstring or create one
                            desc = getattr(attr, "__doc__", None)
                            if not desc:
                                # Try to infer element from ID
                                dot_id = getattr(attr, "id", module_name)
                                if "blazing" in dot_id or "fire" in dot_id:
                                    element = "Fire"
                                elif "frozen" in dot_id or "cold" in dot_id or "ice" in dot_id:
                                    element = "Ice"
                                elif "gale" in dot_id or "wind" in dot_id:
                                    element = "Wind"
                                elif "shadow" in dot_id or "dark" in dot_id or "abyssal" in dot_id:
                                    element = "Dark"
                                elif "charged" in dot_id or "lightning" in dot_id:
                                    element = "Lightning"
                                elif "celestial" in dot_id or "light" in dot_id:
                                    element = "Light"
                                else:
                                    element = "Physical"
                                desc = f"{element}-based damage over time effect."

                            # Determine element from ID
                            dot_id = getattr(attr, "id", module_name)
                            element = "Physical"  # default
                            if any(x in dot_id for x in ["blazing", "fire"]):
                                element = "Fire"
                            elif any(x in dot_id for x in ["frozen", "cold", "ice"]):
                                element = "Ice"
                            elif any(x in dot_id for x in ["gale", "wind"]):
                                element = "Wind"
                            elif any(x in dot_id for x in ["shadow", "dark", "abyssal"]):
                                element = "Dark"
                            elif any(x in dot_id for x in ["charged", "lightning"]):
                                element = "Lightning"
                            elif any(x in dot_id for x in ["celestial", "light"]):
                                element = "Light"
                            elif "poison" in dot_id:
                                element = "Neutral"

                            dot_effects.append({
                                "name": attr_name.replace("_", " ").title(),
                                "type": "DoT" if "weakness" not in dot_id else "Debuff",
                                "description": desc.strip() if desc else f"Damage over time effect: {attr_name}",
                                "element": element
                            })
                            break
                except ImportError:
                    continue

    return jsonify({
        "combat_effects": combat_effects,
        "dot_effects": dot_effects,
        "categories": {
            "combat_effects": "Special effects triggered during combat",
            "dot_effects": "Damage over time and debuff effects",
            "buffs": "Temporary stat boosts and beneficial effects",
            "debuffs": "Negative effects that weaken enemies"
        }
    }), 200


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
