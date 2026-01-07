"""Material crafting and parsing utilities."""

from __future__ import annotations

from plugins import characters as player_plugins

# Constants for new upgrade system
UPGRADEABLE_STATS = [
    "max_hp",
    "atk",
    "defense",
    "crit_rate",
    "crit_damage",
    "vitality",
    "mitigation",
]
# Keep the star-to-material conversion aligned with the per-item unit scale so we
# do not reject valid upgrade requests or lose value when consuming items.
STAR_TO_MATERIALS = {1: 1, 2: 125, 3: 125**2, 4: 125**3}
# Number of 1★ units represented by a single item at each star level.
ITEM_UNIT_SCALE = {
    1: 1,
    2: 125,
    3: 125**2,
    4: 125**3,
}
MATERIAL_STAR_LEVEL = 1


class InsufficientMaterialsError(RuntimeError):
    """Raised when the player does not have enough upgrade materials."""


def _parse_star_level(material_id: str | None) -> int | None:
    """Extract star level from material ID.

    Args:
        material_id: Material identifier (e.g., "fire_3")

    Returns:
        Star level integer or None if parsing fails
    """
    if not material_id:
        return None
    try:
        _, star_raw = str(material_id).rsplit("_", 1)
    except ValueError:
        return None
    try:
        return int(star_raw)
    except (TypeError, ValueError):
        return None


def _canonical_material_breakdown(element_key: str, units: int) -> dict[str, int]:
    """Return a per-tier breakdown for the requested unit cost.

    Args:
        element_key: Element identifier (e.g., "fire")
        units: Total number of 1★ units needed

    Returns:
        Dictionary mapping material IDs to quantities
    """
    breakdown: dict[str, int] = {}
    remaining = max(0, int(units or 0))
    for tier in sorted(ITEM_UNIT_SCALE.keys(), reverse=True):
        item_key = f"{element_key}_{tier}"
        scale = ITEM_UNIT_SCALE[tier]
        if tier == MATERIAL_STAR_LEVEL:
            breakdown[item_key] = remaining
            break
        if scale <= 0 or remaining <= 0:
            breakdown[item_key] = 0
            continue
        count = remaining // scale
        breakdown[item_key] = count
        remaining -= count * scale
    if f"{element_key}_{MATERIAL_STAR_LEVEL}" not in breakdown:
        breakdown[f"{element_key}_{MATERIAL_STAR_LEVEL}"] = remaining
    return breakdown


def _sanitize_breakdown_map(raw_map: dict[str, object] | None) -> dict[str, int]:
    """Sanitize and validate a material breakdown map.

    Args:
        raw_map: Raw material breakdown dictionary

    Returns:
        Cleaned dictionary with valid material IDs and quantities
    """
    if not raw_map:
        return {}
    cleaned: dict[str, int] = {}
    for key, value in raw_map.items():
        try:
            qty = int(value)
        except (TypeError, ValueError):
            continue
        if qty <= 0:
            continue
        cleaned[str(key)] = qty
    return cleaned


def _sum_breakdown_units(breakdown: dict[str, int]) -> int:
    """Calculate total 1★ units from a material breakdown.

    Args:
        breakdown: Material breakdown dictionary

    Returns:
        Total number of 1★ units represented
    """
    total = 0
    for material_id, quantity in breakdown.items():
        tier = _parse_star_level(material_id)
        if tier is None:
            continue
        scale = ITEM_UNIT_SCALE.get(tier)
        if not scale:
            continue
        total += quantity * scale
    return total


def _parse_material_request(
    element_key: str,
    request: object,
) -> tuple[int | None, dict[str, int]]:
    """Extract expected unit totals and per-tier breakdown from a request payload.

    Args:
        element_key: Element identifier
        request: Material request data (int, str, or dict)

    Returns:
        Tuple of (total_units, breakdown_dict)
    """
    if request is None:
        return None, {}

    if isinstance(request, (int, float)) and not isinstance(request, bool):
        units = int(request)
        return units if units >= 0 else None, {}

    if isinstance(request, str):
        try:
            units = int(request.strip())
        except (TypeError, ValueError):
            return None, {}
        return units if units >= 0 else None, {}

    if not isinstance(request, dict):
        return None, {}

    breakdown_source: dict[str, object] | None = None
    for key in ("breakdown", "per_tier", "materials"):
        value = request.get(key)
        if isinstance(value, dict):
            breakdown_source = value
            break

    if breakdown_source is None:
        # Treat the dict as a direct map, omitting metadata keys.
        candidate: dict[str, object] = {}
        for key, value in request.items():
            if key in {"units", "count", "item", "material", "id", "expected"}:
                continue
            candidate[key] = value
        breakdown_source = candidate

    breakdown = _sanitize_breakdown_map(breakdown_source or {})

    units_value = request.get("units")
    if units_value is None:
        units_value = request.get("count")
    if units_value is None and breakdown:
        units_value = _sum_breakdown_units(breakdown)

    if units_value is None:
        return None, breakdown

    try:
        units = int(units_value)
    except (TypeError, ValueError):
        return None, breakdown

    return (units if units >= 0 else None), breakdown


def _get_total_material_units(conn, element_key: str) -> int:
    """Get total available material units for an element.

    Args:
        conn: Database connection
        element_key: Element identifier

    Returns:
        Total number of 1★ units available
    """
    cur = conn.execute(
        "SELECT id, count FROM upgrade_items WHERE id LIKE ?",
        (f"{element_key}_%",),
    )
    total = 0
    for material_id, count in cur.fetchall():
        tier = _parse_star_level(material_id)
        if tier is None:
            continue
        scale = ITEM_UNIT_SCALE.get(tier)
        if not scale:
            continue
        try:
            quantity = int(count)
        except (TypeError, ValueError):
            continue
        if quantity <= 0:
            continue
        total += quantity * scale
    return total


def _consume_material_units(conn, element_key: str, units: int) -> dict[str, int]:
    """Deduct the requested number of 1★ units, converting higher tiers if needed.

    Args:
        conn: Database connection
        element_key: Element identifier
        units: Number of 1★ units to consume

    Returns:
        Dictionary of materials actually spent

    Raises:
        InsufficientMaterialsError: If not enough materials available
    """
    if units <= 0:
        return {}

    total_available = _get_total_material_units(conn, element_key)
    if total_available < units:
        raise InsufficientMaterialsError

    spent: dict[str, int] = {}
    remaining = int(units)
    base_key = f"{element_key}_{MATERIAL_STAR_LEVEL}"

    while remaining > 0:
        candidate: tuple[int, str, int] | None = None
        for tier in sorted(ITEM_UNIT_SCALE.keys(), reverse=True):
            key = f"{element_key}_{tier}"
            scale = ITEM_UNIT_SCALE[tier]
            available_row = conn.execute(
                "SELECT count FROM upgrade_items WHERE id = ?",
                (key,),
            ).fetchone()
            available = int(available_row[0]) if available_row else 0
            if available <= 0:
                continue
            if scale <= remaining or tier == MATERIAL_STAR_LEVEL:
                candidate = (tier, key, scale)
                break

        if candidate:
            tier, key, scale = candidate
            conn.execute(
                "UPDATE upgrade_items SET count = count - 1 WHERE id = ?",
                (key,),
            )
            spent[key] = spent.get(key, 0) + 1
            remaining -= scale
            continue

        # No direct tier matched the remaining amount; convert one higher-tier item.
        convert_candidate: tuple[int, str] | None = None
        for tier in sorted(ITEM_UNIT_SCALE.keys(), reverse=True):
            if tier == MATERIAL_STAR_LEVEL:
                continue
            key = f"{element_key}_{tier}"
            available_row = conn.execute(
                "SELECT count FROM upgrade_items WHERE id = ?",
                (key,),
            ).fetchone()
            available = int(available_row[0]) if available_row else 0
            if available > 0:
                convert_candidate = (tier, key)
                break

        if convert_candidate is None:
            raise InsufficientMaterialsError

        tier, key = convert_candidate
        scale = ITEM_UNIT_SCALE[tier]
        conn.execute(
            "UPDATE upgrade_items SET count = count - 1 WHERE id = ?",
            (key,),
        )
        conn.execute(
            "INSERT OR IGNORE INTO upgrade_items (id, count) VALUES (?, 0)",
            (base_key,),
        )
        conn.execute(
            "UPDATE upgrade_items SET count = count + ? WHERE id = ?",
            (scale, base_key),
        )

    return spent


def _resolve_player_element(conn, player_id: str) -> str:
    """Resolve the active element for a player identifier.

    Args:
        conn: Database connection
        player_id: Player identifier

    Returns:
        Element string (lowercase)
    """
    element = None
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS damage_types (id TEXT PRIMARY KEY, type TEXT)"
        )
        row = conn.execute(
            "SELECT type FROM damage_types WHERE id = ?",
            (player_id,),
        ).fetchone()
        if row and row[0]:
            element = str(row[0])
    except Exception:
        element = None

    if element:
        return element.lower()

    for name in player_plugins.__all__:
        cls = getattr(player_plugins, name)
        if getattr(cls, "id", name) != player_id:
            continue
        inst = cls()
        try:
            return inst.element_id.lower()
        except Exception:
            return str(getattr(inst, "damage_type", "generic")).lower()

    return "generic"
