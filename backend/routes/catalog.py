from __future__ import annotations

from quart import Blueprint
from quart import jsonify
from tracking import log_menu_action
from tracking import log_overlay_action

# Import plugin registries directly to build metadata
from autofighter.cards import _registry as card_registry
from autofighter.relics import _registry as relic_registry

bp = Blueprint("catalog", __name__, url_prefix="/catalog")


@bp.get("/cards")
async def list_cards():
    reg = card_registry()
    cards = []
    for cls in reg.values():
        try:
            c = cls()
            cards.append({
                "id": c.id,
                "name": c.name,
                "stars": c.stars,
                "about": getattr(c, "about", ""),
            })
        except Exception:
            # Skip malformed plugins rather than erroring the whole list
            continue
    payload = {"cards": cards}
    try:
        await log_menu_action("Inventory", "view_cards", {"count": len(cards)})
        await log_overlay_action("inventory", {"section": "cards", "count": len(cards)})
    except Exception:
        pass
    return jsonify(payload)


@bp.get("/relics")
async def list_relics():
    reg = relic_registry()
    relics = []
    for cls in reg.values():
        try:
            r = cls()
            relics.append({
                "id": r.id,
                "name": r.name,
                "stars": r.stars,
                # Base about text; inventory display does not vary by stacks
                "about": getattr(r, "about", ""),
            })
        except Exception:
            continue
    payload = {"relics": relics}
    try:
        await log_menu_action("Inventory", "view_relics", {"count": len(relics)})
        await log_overlay_action("inventory", {"section": "relics", "count": len(relics)})
    except Exception:
        pass
    return jsonify(payload)


@bp.get("/dots")
async def list_dots():
    """Get all available DoT (Damage over Time) effects with descriptions."""
    dots = []

    # Dynamically import DoT classes from plugins
    import importlib.util
    from pathlib import Path

    dots_dir = Path(__file__).parent.parent / "plugins" / "dots"

    if dots_dir.exists():
        for dot_file in dots_dir.glob("*.py"):
            if dot_file.name.startswith("__"):
                continue

            try:
                # Import the module
                spec = importlib.util.spec_from_file_location(
                    f"plugins.dots.{dot_file.stem}", dot_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find DoT classes in the module
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if (hasattr(item, 'plugin_type') and
                        item.plugin_type == 'dot' and
                        hasattr(item, 'id')):

                        # Try to create a dummy instance to get name
                        try:
                            instance = item(1, 1)  # damage=1, turns=1
                            name = getattr(instance, 'name', item.id.replace('_', ' ').title())
                        except Exception:
                            name = item.id.replace('_', ' ').title()

                        # Create description based on damage type
                        description = f"{name} - Damage over time effect"
                        if hasattr(item, '__doc__') and item.__doc__:
                            description = item.__doc__.strip()

                        dots.append({
                            "id": item.id,
                            "name": name,
                            "about": description
                        })

            except Exception:
                # If we can't load a plugin, skip it but don't fail the whole request
                continue

    # Sort by ID for consistent ordering
    dots.sort(key=lambda x: x['id'])

    return jsonify({"dots": dots})


@bp.get("/hots")
async def list_hots():
    """Get all available HoT (Healing over Time) effects with descriptions."""
    hots = []

    # Dynamically import HoT classes from plugins
    import importlib.util
    from pathlib import Path

    hots_dir = Path(__file__).parent.parent / "plugins" / "hots"

    if hots_dir.exists():
        for hot_file in hots_dir.glob("*.py"):
            if hot_file.name.startswith("__"):
                continue

            try:
                # Import the module
                spec = importlib.util.spec_from_file_location(
                    f"plugins.hots.{hot_file.stem}", hot_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find HoT classes in the module
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if (hasattr(item, 'plugin_type') and
                        item.plugin_type == 'hot' and
                        hasattr(item, 'id')):

                        # Try to create a dummy instance to get name
                        try:
                            instance = item(1, 1)  # healing=1, turns=1
                            name = getattr(instance, 'name', item.id.replace('_', ' ').title())
                        except Exception:
                            name = item.id.replace('_', ' ').title()

                        # Create description based on healing type
                        description = f"{name} - Healing over time effect"
                        if hasattr(item, '__doc__') and item.__doc__:
                            description = item.__doc__.strip()

                        hots.append({
                            "id": item.id,
                            "name": name,
                            "about": description
                        })

            except Exception:
                # If we can't load a plugin, skip it but don't fail the whole request
                continue

    # Sort by ID for consistent ordering
    hots.sort(key=lambda x: x['id'])

    return jsonify({"hots": hots})

