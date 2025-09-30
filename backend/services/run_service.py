from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from pathlib import Path
import random
import time
from uuid import uuid4

from battle_logging.writers import end_run_logging
from battle_logging.writers import start_run_logging
from runs.encryption import get_fernet
from runs.encryption import get_save_manager
from runs.lifecycle import battle_snapshots
from runs.lifecycle import emit_battle_end_for_runs
from runs.lifecycle import load_map
from runs.lifecycle import purge_all_run_state
from runs.lifecycle import purge_run_state
from runs.lifecycle import save_map
from runs.party_manager import _assign_damage_type
from runs.party_manager import _describe_passives
from runs.party_manager import _load_player_customization
from runs.party_manager import load_party
from tracking import log_game_action
from tracking import log_menu_action
from tracking import log_play_session_end
from tracking import log_play_session_start
from tracking import log_run_end
from tracking import log_run_start

from autofighter.mapgen import MapGenerator
from autofighter.party import Party
from autofighter.rooms import _choose_foe
from autofighter.rooms import _serialize
from plugins import characters as player_plugins
from services.login_reward_service import record_room_completion
from services.user_level_service import get_user_level

log = logging.getLogger(__name__)


async def _validate_party_members(members: list[str]) -> None:
    if (
        "player" not in members
        or not 1 <= len(members) <= 5
        or len(set(members)) != len(members)
    ):
        raise ValueError("invalid party")

    def get_owned_players():
        with get_save_manager().connection() as conn:
            cur = conn.execute("SELECT id FROM owned_players")
            return {row[0] for row in cur.fetchall()}

    owned = await asyncio.to_thread(get_owned_players)
    for mid in members:
        if mid == "mimic":
            raise ValueError("invalid party")
        if mid != "player" and mid not in owned:
            raise ValueError("unowned character")


async def start_run(
    members: list[str],
    damage_type: str = "",
    pressure: int = 0,
) -> dict[str, object]:
    """Create a new run and return its initial state."""
    damage_type = (damage_type or "").capitalize()

    await _validate_party_members(members)

    if damage_type:
        allowed = {"Light", "Dark", "Wind", "Lightning", "Fire", "Ice"}
        if damage_type not in allowed:
            raise ValueError("invalid damage type")

        def set_damage_type():
            with get_save_manager().connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO damage_types (id, type) VALUES (?, ?)",
                    ("player", damage_type),
                )

        await asyncio.to_thread(set_damage_type)

    run_id = str(uuid4())
    start_ts = int(time.time())
    start_run_logging(run_id)

    party_members: list[player_plugins._base.PlayerBase] = []
    party_info: list[dict[str, object]] = []
    for pid in members:
        for name in player_plugins.__all__:
            cls = getattr(player_plugins, name)
            if cls.id == pid:
                inst = cls()
                inst.exp = 0
                inst.level = 1
                _assign_damage_type(inst)
                party_members.append(inst)
                party_info.append(
                    {
                        "id": inst.id,
                        "name": inst.name,
                        "passives": _describe_passives(inst),
                        "exp": inst.exp,
                        "level": inst.level,
                    }
                )
                break

    initial_party = Party(
        members=party_members,
        gold=0,
        relics=[],
        cards=[],
        rdr=1.0,
    )

    generator = MapGenerator(run_id, pressure=pressure)
    nodes = generator.generate_floor(party=initial_party)

    boss_choice = None
    if initial_party.members and nodes:
        boss_choice = _choose_foe(nodes[-1], initial_party)

    state = {
        "rooms": [n.to_dict() for n in nodes],
        "current": 1,
        "battle": False,
        "awaiting_card": False,
        "awaiting_relic": False,
        "awaiting_loot": False,
        "awaiting_next": False,
        "total_rooms_cleared": 0,
        "floors_cleared": 0,
        "current_pressure": int(pressure or 0),
    }
    if boss_choice is not None and nodes:
        state["floor_boss"] = {
            "id": getattr(boss_choice, "id", type(boss_choice).__name__),
            "floor": getattr(nodes[-1], "floor", 1),
            "loop": getattr(nodes[-1], "loop", 1),
        }
    pronouns, stats = await asyncio.to_thread(_load_player_customization)

    def get_player_damage_type():
        with get_save_manager().connection() as conn:
            cur = conn.execute(
                "SELECT type FROM damage_types WHERE id = ?",
                ("player",),
            )
            return cur.fetchone()

    row = await asyncio.to_thread(get_player_damage_type)
    player_type = row[0] if row else player_plugins.player.Player().element_id
    snapshot = {
        "pronouns": pronouns,
        "damage_type": player_type,
        "stats": stats,
    }

    def save_new_run():
        with get_save_manager().connection() as conn:
            conn.execute(
                "INSERT INTO runs (id, party, map) VALUES (?, ?, ?)",
                (
                    run_id,
                    json.dumps(
                        {
                            "members": members,
                            "gold": 0,
                            "relics": [],
                            "cards": [],
                            "exp": dict.fromkeys(members, 0),
                            "level": dict.fromkeys(members, 1),
                            "rdr": 1.0,
                            # Freeze the user level for the duration of this run
                            "user_level": int(get_user_level()),
                            "player": snapshot,
                        }
                    ),
                    json.dumps(state),
                ),
            )

    await asyncio.to_thread(save_new_run)

    member_snapshots: list[dict[str, object]] = []
    for slot, member in enumerate(party_members):
        try:
            stats = _serialize(member)
        except Exception:  # pragma: no cover - defensive serialization fallback
            stats = {"id": getattr(member, "id", f"member-{slot}")}
        member_snapshots.append(
            {
                "slot": slot,
                "character_id": getattr(member, "id", f"member-{slot}"),
                "stats": stats,
            }
        )

    await log_run_start(run_id, start_ts, member_snapshots)
    await log_play_session_start(run_id, "local", start_ts)
    await log_menu_action(
        "Run",
        "started",
        {
            "members": members,
            "damage_type": damage_type,
            "pressure": pressure,
            "run_id": run_id,
        },
    )
    return {"run_id": run_id, "map": state, "party": party_info}


async def update_party(run_id: str, members: list[str]) -> dict[str, object]:
    """Update an existing run's party roster after validating membership."""

    await _validate_party_members(members)

    def update_roster() -> dict[str, object]:
        with get_save_manager().connection() as conn:
            cur = conn.execute("SELECT party FROM runs WHERE id = ?", (run_id,))
            row = cur.fetchone()
            if not row:
                raise LookupError("run not found")

            party_blob = json.loads(row[0]) if row[0] else {}
            snapshot = party_blob.get("player", {})
            exp_source = party_blob.get("exp", {})
            level_source = party_blob.get("level", {})
            multiplier_source = party_blob.get("exp_multiplier", {})

            exp = {mid: exp_source.get(mid, 0) for mid in members}
            level = {mid: level_source.get(mid, 1) for mid in members}
            exp_multiplier = {mid: multiplier_source.get(mid, 1.0) for mid in members}

            party_blob.update(
                {
                    "members": members,
                    "exp": exp,
                    "level": level,
                    "exp_multiplier": exp_multiplier,
                    "player": snapshot,
                }
            )

            conn.execute(
                "UPDATE runs SET party = ? WHERE id = ?",
                (json.dumps(party_blob), run_id),
            )

            return party_blob

    updated = await asyncio.to_thread(update_roster)
    await log_menu_action(
        "Run",
        "party_updated",
        {"run_id": run_id, "members": members},
    )
    return updated


async def get_map(run_id: str) -> dict[str, object]:
    try:
        from battle_logging.writers import get_current_run_logger  # local import
        logger = get_current_run_logger()
        if logger is None or getattr(logger, "run_id", None) != run_id:
            start_run_logging(run_id)
    except Exception:
        pass
    state, rooms = await asyncio.to_thread(load_map, run_id)
    if not state:
        raise ValueError("run not found")

    def get_party_data():
        with get_save_manager().connection() as conn:
            cur = conn.execute("SELECT party FROM runs WHERE id = ?", (run_id,))
            row = cur.fetchone()
            return json.loads(row[0]) if row and row[0] else {}

    party_state = await asyncio.to_thread(get_party_data)

    current_index = int(state.get("current", 0))
    current_room_data = None
    current_room_type = None
    next_room_type = None

    if rooms and 0 <= current_index < len(rooms):
        current_node = rooms[current_index]
        current_room_type = current_node.room_type
        if current_index + 1 < len(rooms):
            next_room_type = rooms[current_index + 1].room_type
        snap = battle_snapshots.get(run_id)
        if snap is not None and current_room_type in {
            "battle-weak",
            "battle-normal",
            "battle-boss-floor",
        }:
            current_room_data = snap
        elif state.get("awaiting_next"):
            result = (
                "boss"
                if current_room_type == "battle-boss-floor"
                else current_room_type.replace("-", "_") if current_room_type else "unknown"
            )
            current_room_data = {
                "result": result,
                "awaiting_next": True,
                "current_index": current_index,
                "current_room": current_room_type,
                "next_room": next_room_type,
            }

    return {
        "map": state,
        "party": party_state.get("members", []),
        "current_state": {
            "current_index": current_index,
            "current_room_type": current_room_type,
            "next_room_type": next_room_type,
            "awaiting_next": state.get("awaiting_next", False),
            "awaiting_card": state.get("awaiting_card", False),
            "awaiting_relic": state.get("awaiting_relic", False),
            "awaiting_loot": state.get("awaiting_loot", False),
            "room_data": current_room_data,
        },
    }


async def advance_room(run_id: str) -> dict[str, object]:
    state, rooms = await asyncio.to_thread(load_map, run_id)
    if not rooms:
        raise ValueError("run not found")

    current_index = int(state.get("current", 0))
    current_room = rooms[current_index] if 0 <= current_index < len(rooms) else None

    if (
        state.get("awaiting_card")
        or state.get("awaiting_relic")
        or state.get("awaiting_loot")
    ):
        raise ValueError("pending rewards must be collected before advancing")

    # Reset live battle state when advancing
    purge_run_state(run_id)

    previous_index = int(state.get("current", 0))
    total_rooms_cleared = int(state.get("total_rooms_cleared", 0))
    if 0 < previous_index < len(rooms):
        total_rooms_cleared += 1
    state["total_rooms_cleared"] = total_rooms_cleared

    state["current"] += 1
    state["awaiting_next"] = False

    if state["current"] >= len(rooms):
        try:
            last = rooms[-1]
            next_floor = int(getattr(last, "floor", 1)) + 1
            loop = int(getattr(last, "loop", 1))
            pressure = int(getattr(last, "pressure", 0))
        except Exception:
            next_floor, loop, pressure = 1, 1, 0

        try:
            party = await asyncio.to_thread(load_party, run_id)
        except Exception:
            party = None

        generator = MapGenerator(
            f"{run_id}-floor-{next_floor}", floor=next_floor, loop=loop, pressure=pressure
        )
        nodes = generator.generate_floor(party=party)
        state["rooms"] = [n.to_dict() for n in nodes]
        state["current"] = 1
        state["floors_cleared"] = int(state.get("floors_cleared", 0)) + 1
        state["current_pressure"] = int(getattr(nodes[-1], "pressure", pressure)) if nodes else int(pressure)
        new_floor = getattr(nodes[-1], "floor", next_floor) if nodes else next_floor
        new_loop = getattr(nodes[-1], "loop", loop) if nodes else loop
        if party and party.members and nodes:
            boss_node = nodes[-1]
            tracker_data = state.get("boss_spawn_tracker")
            if isinstance(tracker_data, dict):
                boss_spawn_tracker: dict[str, dict[str, int]] = tracker_data
            else:
                boss_spawn_tracker = {}
                state["boss_spawn_tracker"] = boss_spawn_tracker
            setattr(boss_node, "boss_spawn_tracker", boss_spawn_tracker)
            try:
                floors_cleared = int(state.get("floors_cleared", 0))
            except Exception:
                floors_cleared = 0
            current_boss_floor_number = max(floors_cleared, 0) + 1
            setattr(boss_node, "boss_floor_number", current_boss_floor_number)
            boss_choice = _choose_foe(boss_node, party)
            state["floor_boss"] = {
                "id": getattr(boss_choice, "id", type(boss_choice).__name__),
                "floor": new_floor,
                "loop": new_loop,
            }
        else:
            state.pop("floor_boss", None)
        next_type = nodes[state["current"]].room_type if state["current"] < len(nodes) else None
    else:
        next_type = (
            rooms[state["current"]].room_type if state["current"] < len(rooms) else None
        )
        if state["current"] < len(rooms):
            state["current_pressure"] = int(
                getattr(rooms[state["current"]], "pressure", state.get("current_pressure", 0))
            )

    await asyncio.to_thread(save_map, run_id, state)
    try:
        await record_room_completion()
    except Exception:
        pass
    payload = {"next_room": next_type, "current_index": state["current"]}
    try:
        await log_game_action(
            "advance_room",
            run_id=run_id,
            room_id=str(getattr(current_room, "room_id", getattr(current_room, "index", ""))),
            details={
                "next_room": next_type,
                "floors_cleared": state.get("floors_cleared"),
                "total_rooms_cleared": state.get("total_rooms_cleared"),
            },
        )
    except Exception:  # pragma: no cover - telemetry should not break gameplay
        log.debug("Failed to log advance_room telemetry", exc_info=True)
    return payload


async def get_battle_summary(run_id: str, index: int) -> dict[str, object] | None:
    base = Path(__file__).resolve().parents[1]
    primary = base / "logs" / "runs" / run_id / "battles" / str(index) / "summary" / "battle_summary.json"
    # Backward-compat: older writers used backend/battle_logging/logs
    fallback = base / "battle_logging" / "logs" / "runs" / run_id / "battles" / str(index) / "summary" / "battle_summary.json"
    summary_path = primary if primary.exists() else fallback
    if not summary_path.exists():
        return None
    data = await asyncio.to_thread(summary_path.read_text)
    return json.loads(data)


async def get_battle_events(run_id: str, index: int) -> dict[str, object] | None:
    base = Path(__file__).resolve().parents[1]
    primary = base / "logs" / "runs" / run_id / "battles" / str(index) / "summary" / "events.json"
    # Backward-compat: older writers used backend/battle_logging/logs
    fallback = base / "battle_logging" / "logs" / "runs" / run_id / "battles" / str(index) / "summary" / "events.json"
    events_path = primary if primary.exists() else fallback
    if not events_path.exists():
        return None
    data = await asyncio.to_thread(events_path.read_text)
    return json.loads(data)


async def shutdown_run(run_id: str) -> bool:
    """Terminate a run and clear associated state.

    Returns True when the run existed and was removed; False when the run could not
    be found. Any other exception bubbles up to the caller.
    """

    def delete_run() -> bool:
        with get_save_manager().connection() as conn:
            cur = conn.execute("SELECT id FROM runs WHERE id = ?", (run_id,))
            if not cur.fetchone():
                return False

            conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
            return True

    end_run_logging()

    await emit_battle_end_for_runs([run_id])

    existed = await asyncio.to_thread(delete_run)
    if not existed:
        return False

    purge_run_state(run_id)

    await log_run_end(run_id, "aborted")
    await log_play_session_end(run_id)
    await log_menu_action("Run", "ended", {"run_id": run_id})

    return True


async def wipe_save() -> None:
    def do_wipe():
        manager = get_save_manager()
        manager.db_path.unlink(missing_ok=True)
        manager.migrate(Path(__file__).resolve().parent.parent / "migrations")
        persona = random.choice(["lady_darkness", "lady_light"])
        with manager.connection() as conn:
            conn.execute("INSERT INTO owned_players (id) VALUES (?)", (persona,))
            conn.execute(
                "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS damage_types (id TEXT PRIMARY KEY, type TEXT)"
            )

    await emit_battle_end_for_runs()
    purge_all_run_state()
    await asyncio.to_thread(do_wipe)


async def backup_save() -> bytes:
    def get_backup_data():
        with get_save_manager().connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS damage_types (id TEXT PRIMARY KEY, type TEXT)"
            )
            runs = conn.execute("SELECT id, party, map FROM runs").fetchall()
            options = conn.execute("SELECT key, value FROM options").fetchall()
            dmg = conn.execute("SELECT id, type FROM damage_types").fetchall()
        return {"runs": runs, "options": options, "damage_types": dmg}

    payload = await asyncio.to_thread(get_backup_data)
    data = json.dumps(payload)
    digest = hashlib.sha256(data.encode()).hexdigest()
    package = json.dumps({"hash": digest, "data": data}).encode()
    token = get_fernet().encrypt(package)
    return token


async def restore_save(blob: bytes) -> None:
    try:
        package = get_fernet().decrypt(blob)
        obj = json.loads(package)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("invalid backup") from exc
    data = obj.get("data", "")
    digest = obj.get("hash", "")
    if hashlib.sha256(data.encode()).hexdigest() != digest:
        raise ValueError("hash mismatch")
    payload = json.loads(data)

    def restore_data():
        with get_save_manager().connection() as conn:
            conn.execute("DELETE FROM runs")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
            )
            conn.execute("DELETE FROM options")
            conn.execute(
                "CREATE TABLE IF NOT EXISTS damage_types (id TEXT PRIMARY KEY, type TEXT)"
            )
            conn.execute("DELETE FROM damage_types")
            conn.executemany(
                "INSERT INTO runs (id, party, map) VALUES (?, ?, ?)", payload["runs"]
            )
            conn.executemany(
                "INSERT INTO options (key, value) VALUES (?, ?)", payload["options"]
            )
            conn.executemany(
                "INSERT INTO damage_types (id, type) VALUES (?, ?)", payload["damage_types"]
            )

    await emit_battle_end_for_runs()
    purge_all_run_state()
    await asyncio.to_thread(restore_data)
