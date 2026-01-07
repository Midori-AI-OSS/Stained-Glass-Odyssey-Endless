"""Upgrade utility functions for player stat upgrades."""

from __future__ import annotations

import math
from typing import Dict
from typing import List

from runs.encryption import get_save_manager

from .materials import MATERIAL_STAR_LEVEL
from .materials import UPGRADEABLE_STATS
from .materials import _canonical_material_breakdown
from .materials import _resolve_player_element


def _estimate_cost_from_upgrade_percent(upgrade_percent: object) -> int | None:
    """Translate a stored percent boost back into spent upgrade points.

    Args:
        upgrade_percent: Upgrade percentage value

    Returns:
        Estimated cost in points or None if invalid
    """
    try:
        percent = float(upgrade_percent)
    except (TypeError, ValueError):
        return None

    if percent <= 0:
        return None

    points = int(round(percent * 1000))
    return points if points > 0 else None


def _backfill_upgrade_costs(conn) -> None:
    """Populate missing ``cost_spent`` values for legacy upgrade rows.

    Args:
        conn: Database connection
    """
    cur = conn.execute(
        """
        SELECT id, player_id, stat_name, upgrade_percent, cost_spent, source_star
        FROM player_stat_upgrades
        ORDER BY player_id ASC, stat_name ASC, created_at ASC, id ASC
        """
    )

    updates: list[tuple[int, int]] = []
    stat_counts: dict[tuple[str, str], int] = {}

    for row in cur.fetchall():
        upgrade_id, player_id, stat_name, upgrade_percent, cost_spent, source_star = row

        if not player_id or not stat_name:
            continue

        key = (str(player_id), str(stat_name))
        upgrade_count = stat_counts.get(key, 0)

        try:
            source_value = int(source_star)
        except (TypeError, ValueError):
            source_value = 1

        if source_value <= 0:
            stat_counts[key] = upgrade_count + 1
            continue

        if cost_spent and cost_spent > 0:
            stat_counts[key] = upgrade_count + 1
            continue

        estimated_points = _estimate_cost_from_upgrade_percent(upgrade_percent)
        if estimated_points is None:
            estimated_points = upgrade_count + 1

        stat_counts[key] = upgrade_count + 1
        updates.append((int(estimated_points), upgrade_id))

    if updates:
        conn.executemany(
            "UPDATE player_stat_upgrades SET cost_spent = ? WHERE id = ?",
            updates,
        )


def _migrate_legacy_points(conn) -> None:
    """Convert legacy upgrade points into 1★ materials.

    Args:
        conn: Database connection
    """
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'player_upgrade_points'"
    )
    if cur.fetchone() is None:
        return

    rows = conn.execute(
        "SELECT player_id, points FROM player_upgrade_points"
    ).fetchall()
    for player_id, points in rows:
        try:
            material_count = int(points)
        except (TypeError, ValueError):
            material_count = 0
        if material_count <= 0:
            continue
        element = _resolve_player_element(conn, str(player_id))
        item_key = f"{element}_{MATERIAL_STAR_LEVEL}"
        current = conn.execute(
            "SELECT count FROM upgrade_items WHERE id = ?",
            (item_key,),
        ).fetchone()
        existing = int(current[0]) if current else 0
        conn.execute(
            "INSERT OR REPLACE INTO upgrade_items (id, count) VALUES (?, ?)",
            (item_key, existing + material_count),
        )

    conn.execute("DROP TABLE IF EXISTS player_upgrade_points")


def _ensure_upgrade_tables(conn) -> None:
    """Ensure upgrade tables exist and have required columns.

    Args:
        conn: Database connection
    """
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS player_stat_upgrades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id TEXT NOT NULL,
            stat_name TEXT NOT NULL,
            upgrade_percent REAL NOT NULL,
            source_star INTEGER NOT NULL,
            cost_spent INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS upgrade_items (id TEXT PRIMARY KEY, count INTEGER NOT NULL)"
    )

    cur = conn.execute("PRAGMA table_info(player_stat_upgrades)")
    columns = {row[1] for row in cur.fetchall()}
    has_source_star = "source_star" in columns
    if not has_source_star:
        conn.execute(
            "ALTER TABLE player_stat_upgrades ADD COLUMN source_star INTEGER NOT NULL DEFAULT 0"
        )
        has_source_star = True
    needs_backfill = False
    if "cost_spent" not in columns:
        conn.execute(
            "ALTER TABLE player_stat_upgrades ADD COLUMN cost_spent INTEGER NOT NULL DEFAULT 0"
        )
        needs_backfill = True

    if not needs_backfill:
        if has_source_star:
            cur = conn.execute(
                """
                SELECT 1
                FROM player_stat_upgrades
                WHERE (cost_spent IS NULL OR cost_spent <= 0) AND source_star > 0
                LIMIT 1
                """
            )
        else:
            cur = conn.execute(
                "SELECT 1 FROM player_stat_upgrades WHERE cost_spent <= 0 LIMIT 1"
            )
        needs_backfill = cur.fetchone() is not None

    if needs_backfill:
        _backfill_upgrade_costs(conn)

    _migrate_legacy_points(conn)


def _create_upgrade_tables():
    """Create upgrade tables if they don't exist."""
    with get_save_manager().connection() as conn:
        _ensure_upgrade_tables(conn)
        conn.commit()


def _get_player_stat_upgrades(player_id: str) -> List[Dict]:
    """Get all stat upgrades for a player.

    Args:
        player_id: Player identifier

    Returns:
        List of upgrade dictionaries
    """
    with get_save_manager().connection() as conn:
        _ensure_upgrade_tables(conn)
        cur = conn.execute("""
            SELECT id, stat_name, upgrade_percent, source_star, cost_spent, created_at
            FROM player_stat_upgrades
            WHERE player_id = ?
            ORDER BY created_at DESC, id DESC
        """, (player_id,))
        return [
            {
                "id": row[0],
                "stat_name": row[1],
                "upgrade_percent": row[2],
                "source_star": row[3],
                "cost_spent": row[4],
                "created_at": row[5]
            }
            for row in cur.fetchall()
        ]


def _count_completed_upgrades(stat_upgrades: List[Dict]) -> Dict[str, int]:
    """Count completed upgrades per stat.

    Args:
        stat_upgrades: List of upgrade dictionaries

    Returns:
        Dictionary mapping stat names to upgrade counts
    """
    counts: Dict[str, int] = {stat: 0 for stat in UPGRADEABLE_STATS}
    for upgrade in stat_upgrades:
        stat_name = upgrade.get("stat_name")
        if stat_name is None:
            continue
        counts[stat_name] = counts.get(stat_name, 0) + 1
    return counts


def _calculate_next_cost(last_cost: int | None) -> int:
    """Calculate next upgrade cost with 5% scaling.

    Args:
        last_cost: Last upgrade cost

    Returns:
        Next upgrade cost (minimum 1)
    """
    if not last_cost or last_cost < 1:
        return 1
    return max(1, math.ceil(last_cost * 1.05))


def _determine_next_costs(stat_upgrades: List[Dict], element_key: str) -> Dict[str, dict[str, object]]:
    """Determine next upgrade costs for all stats.

    Args:
        stat_upgrades: List of existing upgrades
        element_key: Element identifier

    Returns:
        Dictionary mapping stat names to cost payloads
    """
    last_costs: Dict[str, int] = {}
    for upgrade in stat_upgrades:
        stat_name = upgrade.get("stat_name")
        if stat_name is None or stat_name in last_costs:
            continue
        try:
            raw_cost = upgrade.get("cost_spent")
            if raw_cost in (None, 0):
                raw_cost = upgrade.get("materials_spent")
            if raw_cost in (None, 0):
                percent_value = float(upgrade.get("upgrade_percent") or 0.0)
                raw_cost = int(round(percent_value * 1000))
            last_costs[stat_name] = int(raw_cost or 0)
        except (TypeError, ValueError):
            last_costs[stat_name] = 0

    def _build_cost_payload(units: int) -> dict[str, object]:
        breakdown = _canonical_material_breakdown(element_key, units)
        return {
            "item": f"{element_key}_{MATERIAL_STAR_LEVEL}",
            "units": units,
            "breakdown": breakdown,
        }

    next_costs: Dict[str, dict[str, object]] = {}
    seen_stats = set(UPGRADEABLE_STATS)
    for stat in UPGRADEABLE_STATS:
        units = _calculate_next_cost(last_costs.get(stat))
        next_costs[stat] = _build_cost_payload(units)
    for stat, last_cost in last_costs.items():
        if stat in seen_stats:
            continue
        units = _calculate_next_cost(last_cost)
        next_costs[stat] = _build_cost_payload(units)
    return next_costs


def _get_next_cost_for_stat(player_id: str, stat_name: str, *, conn=None) -> int:
    """Get next upgrade cost for a specific stat.

    Args:
        player_id: Player identifier
        stat_name: Stat name
        conn: Optional database connection

    Returns:
        Next upgrade cost
    """
    def _resolve_last_cost(row) -> int:
        if not row:
            return 0
        cost_spent, upgrade_percent = row
        try:
            if cost_spent and int(cost_spent) > 0:
                return int(cost_spent)
        except (TypeError, ValueError):
            pass
        try:
            percent_value = float(upgrade_percent or 0.0)
        except (TypeError, ValueError):
            percent_value = 0.0
        estimated = int(round(percent_value * 1000))
        return max(0, estimated)

    if conn is None:
        with get_save_manager().connection() as local_conn:
            _ensure_upgrade_tables(local_conn)
            cur = local_conn.execute(
                """
                SELECT cost_spent, upgrade_percent
                FROM player_stat_upgrades
                WHERE player_id = ? AND stat_name = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (player_id, stat_name),
            )
            last_cost = _resolve_last_cost(cur.fetchone())
            return _calculate_next_cost(last_cost)

    cur = conn.execute(
        """
        SELECT cost_spent, upgrade_percent
        FROM player_stat_upgrades
        WHERE player_id = ? AND stat_name = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (player_id, stat_name),
    )
    last_cost = _resolve_last_cost(cur.fetchone())
    return _calculate_next_cost(last_cost)


def _build_player_upgrade_payload(player_id: str) -> Dict:
    """Build complete upgrade payload for a player.

    Args:
        player_id: Player identifier

    Returns:
        Dictionary with stat_upgrades, stat_totals, stat_counts, next_costs, element
    """
    stat_upgrades_raw = _get_player_stat_upgrades(player_id)
    stat_upgrades: List[Dict] = []
    for upgrade in stat_upgrades_raw:
        converted = dict(upgrade)
        converted["materials_spent"] = converted.pop("cost_spent", 0)
        stat_upgrades.append(converted)

    stat_totals: Dict[str, float] = {stat: 0.0 for stat in UPGRADEABLE_STATS}
    for upgrade in stat_upgrades:
        stat_name = upgrade.get("stat_name")
        if stat_name is None:
            continue
        stat_totals[stat_name] = stat_totals.get(stat_name, 0.0) + float(
            upgrade.get("upgrade_percent") or 0.0
        )

    stat_counts = _count_completed_upgrades(stat_upgrades)

    with get_save_manager().connection() as conn:
        _ensure_upgrade_tables(conn)
        element = _resolve_player_element(conn, player_id)

    next_costs = _determine_next_costs(stat_upgrades, element)

    for stat in UPGRADEABLE_STATS:
        stat_totals.setdefault(stat, 0.0)
        if stat not in next_costs:
            units = _calculate_next_cost(None)
            next_costs[stat] = {
                "item": f"{element}_{MATERIAL_STAR_LEVEL}",
                "units": units,
                "breakdown": _canonical_material_breakdown(element, units),
            }

    return {
        "stat_upgrades": stat_upgrades,
        "stat_totals": stat_totals,
        "stat_counts": stat_counts,
        "next_costs": next_costs,
        "element": element,
    }
