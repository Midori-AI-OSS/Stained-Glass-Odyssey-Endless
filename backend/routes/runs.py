from __future__ import annotations

import asyncio
import hashlib
import json
import random
from pathlib import Path
from uuid import uuid4

from quart import Blueprint
from quart import jsonify
from quart import request

from plugins import players as player_plugins
from autofighter.mapgen import MapGenerator

from game import FERNET
from game import load_map
from game import save_map
from game import battle_tasks
from game import SAVE_MANAGER
from game import _passive_names
from game import battle_snapshots
from game import _assign_damage_type
from game import _load_player_customization

bp = Blueprint("runs", __name__)


@bp.post("/run/start")
async def start_run() -> tuple[str, int, dict[str, object]]:
    data = await request.get_json(silent=True) or {}
    members: list[str] = data.get("party", [])
    damage_type = (data.get("damage_type") or "").capitalize()
    if (
        "player" not in members
        or not 1 <= len(members) <= 5
        or len(set(members)) != len(members)
    ):
        return jsonify({"error": "invalid party"}), 400
    with SAVE_MANAGER.connection() as conn:
        cur = conn.execute("SELECT id FROM owned_players")
        owned = {row[0] for row in cur.fetchall()}
    for mid in members:
        if mid != "player" and mid not in owned:
            return jsonify({"error": "unowned character"}), 400
    if damage_type:
        allowed = {"Light", "Dark", "Wind", "Lightning", "Fire", "Ice"}
        if damage_type not in allowed:
            return jsonify({"error": "invalid damage type"}), 400
        with SAVE_MANAGER.connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO damage_types (id, type) VALUES (?, ?)",
                ("player", damage_type),
            )
    run_id = str(uuid4())
    generator = MapGenerator(run_id)
    nodes = generator.generate_floor()
    state = {
        "rooms": [n.to_dict() for n in nodes],
        "current": 1,
        "battle": False,
        "awaiting_card": False,
        "awaiting_relic": False,
        "awaiting_next": False,
    }
    pronouns, stats = _load_player_customization()
    with SAVE_MANAGER.connection() as conn:
        cur = conn.execute(
            "SELECT type FROM damage_types WHERE id = ?",
            ("player",),
        )
        row = cur.fetchone()
    player_type = row[0] if row else player_plugins.player.Player().element_id
    snapshot = {
        "pronouns": pronouns,
        "damage_type": player_type,
        "stats": stats,
    }
    with SAVE_MANAGER.connection() as conn:
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
                        "exp": {pid: 0 for pid in members},
                        "level": {pid: 1 for pid in members},
                        "rdr": 1.0,
                        "player": snapshot,
                    }
                ),
                json.dumps(state),
            ),
        )
    party_info: list[dict[str, object]] = []
    for pid in members:
        for name in player_plugins.__all__:
            cls = getattr(player_plugins, name)
            if cls.id == pid:
                inst = cls()
                inst.exp = 0
                inst.level = 1
                _assign_damage_type(inst)
                party_info.append(
                    {
                        "id": inst.id,
                        "name": inst.name,
                        "passives": _passive_names(getattr(inst, "passives", [])),
                        "exp": inst.exp,
                        "level": inst.level,
                    }
                )
                break
    return jsonify({"run_id": run_id, "map": state, "party": party_info})


@bp.put("/party/<run_id>")
async def update_party(run_id: str) -> tuple[str, int, dict[str, object]]:
    data = await request.get_json(silent=True) or {}
    members = data.get("party", [])
    gold = data.get("gold", 0)
    relics = data.get("relics", [])
    cards = data.get("cards", [])
    rdr = data.get("rdr", 1.0)
    if (
        "player" not in members
        or not 1 <= len(members) <= 5
        or len(set(members)) != len(members)
    ):
        return jsonify({"error": "invalid party"}), 400
    with SAVE_MANAGER.connection() as conn:
        cur = conn.execute("SELECT id FROM owned_players")
        owned = {row[0] for row in cur.fetchall()}
    for mid in members:
        if mid != "player" and mid not in owned:
            return jsonify({"error": "unowned character"}), 400
    party = {
        "members": members,
        "gold": gold,
        "relics": relics,
        "cards": cards,
        "exp": {pid: 0 for pid in members},
        "level": {pid: 1 for pid in members},
        "rdr": rdr,
    }
    with SAVE_MANAGER.connection() as conn:
        conn.execute(
            "UPDATE runs SET party = ? WHERE id = ?",
            (json.dumps(party), run_id),
        )
    return jsonify({"party": members})


@bp.get("/map/<run_id>")
async def get_map(run_id: str) -> tuple[str, int, dict[str, object]]:
    with SAVE_MANAGER.connection() as conn:
        cur = conn.execute("SELECT map, party FROM runs WHERE id = ?", (run_id,))
        row = cur.fetchone()
    if row is None:
        return jsonify({"error": "run not found"}), 404
    map_state = json.loads(row[0])
    party_state = json.loads(row[1]) if row[1] else {}
    return jsonify({"map": map_state, "party": party_state.get("members", [])})


@bp.delete("/run/<run_id>")
async def end_run(run_id: str) -> tuple[str, int, dict[str, str]]:
    task = battle_tasks.pop(run_id, None)
    try:
        if task is not None and not task.done():
            task.cancel()
            try:
                await asyncio.sleep(0)
            except Exception:
                pass
    except Exception:
        pass
    battle_snapshots.pop(run_id, None)
    with SAVE_MANAGER.connection() as conn:
        cur = conn.execute("DELETE FROM runs WHERE id = ?", (run_id,))
        if cur.rowcount == 0:
            return jsonify({"error": "run not found"}), 404
    return jsonify({"status": "ended"})


@bp.post("/run/<run_id>/next")
async def advance_room(run_id: str) -> tuple[str, int, dict[str, object]]:
    state, rooms = load_map(run_id)
    if state.get("awaiting_card") or state.get("awaiting_relic"):
        return jsonify({"error": "awaiting reward"}), 400
    if not state.get("awaiting_next"):
        return jsonify({"error": "not ready"}), 400
    state["current"] += 1
    state["awaiting_next"] = False
    next_type = (
        rooms[state["current"]].room_type if state["current"] < len(rooms) else None
    )
    save_map(run_id, state)
    return jsonify({"next_room": next_type, "current_index": state["current"]})


@bp.post("/save/wipe")
async def wipe_save() -> tuple[str, int, dict[str, str]]:
    SAVE_MANAGER.db_path.unlink(missing_ok=True)
    SAVE_MANAGER.migrate(Path(__file__).resolve().parent / "migrations")
    persona = random.choice(["lady_darkness", "lady_light"])
    with SAVE_MANAGER.connection() as conn:
        conn.execute("INSERT INTO owned_players (id) VALUES (?)", (persona,))
        conn.execute(
            "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS damage_types (id TEXT PRIMARY KEY, type TEXT)"
        )
    return jsonify({"status": "wiped"})


@bp.get("/save/backup")
async def backup_save() -> tuple[bytes, int, dict[str, str]]:
    with SAVE_MANAGER.connection() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS damage_types (id TEXT PRIMARY KEY, type TEXT)"
        )
        runs = conn.execute("SELECT id, party, map FROM runs").fetchall()
        options = conn.execute("SELECT key, value FROM options").fetchall()
        dmg = conn.execute("SELECT id, type FROM damage_types").fetchall()
    payload = {"runs": runs, "options": options, "damage_types": dmg}
    data = json.dumps(payload)
    digest = hashlib.sha256(data.encode()).hexdigest()
    package = json.dumps({"hash": digest, "data": data}).encode()
    token = FERNET.encrypt(package)
    headers = {
        "Content-Type": "application/octet-stream",
        "Content-Disposition": "attachment; filename=backup.afsave",
    }
    return token, 200, headers


@bp.post("/save/restore")
async def restore_save() -> tuple[str, int, dict[str, str]]:
    blob = await request.get_data()
    try:
        package = FERNET.decrypt(blob)
        obj = json.loads(package)
    except Exception:
        return jsonify({"error": "invalid backup"}), 400
    data = obj.get("data", "")
    digest = obj.get("hash", "")
    if hashlib.sha256(data.encode()).hexdigest() != digest:
        return jsonify({"error": "hash mismatch"}), 400
    payload = json.loads(data)
    with SAVE_MANAGER.connection() as conn:
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
    return jsonify({"status": "restored"})
