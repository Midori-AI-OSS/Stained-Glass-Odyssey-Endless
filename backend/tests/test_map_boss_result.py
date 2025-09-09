import asyncio
import json
import os
from pathlib import Path
import tempfile
import time

import game
from game import get_save_manager
from services.run_service import get_map


def test_get_map_returns_boss_for_awaiting_next_boss_room() -> None:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        db_path = Path(tmp_db.name)
    try:
        original_db_url = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        game.SAVE_MANAGER = None
        game.FERNET = None
        manager = get_save_manager()

        run_id = f"test-boss-map-{int(time.time())}"
        party_data = {
            "members": ["player"],
            "gold": 0,
            "relics": [],
            "cards": [],
            "exp": {"player": 0},
            "level": {"player": 1},
            "rdr": 1.0,
            "player": {
                "pronouns": "",
                "damage_type": "Light",
                "stats": {"hp": 0, "attack": 0, "defense": 0},
            },
        }
        map_data = {
            "rooms": [
                {
                    "room_type": "start",
                    "floor": 1,
                    "index": 0,
                    "room_id": 0,
                    "loop": 1,
                    "pressure": 0,
                },
                {
                    "room_type": "battle-boss-floor",
                    "floor": 1,
                    "index": 1,
                    "room_id": 1,
                    "loop": 1,
                    "pressure": 0,
                },
            ],
            "current": 1,
            "battle": False,
            "awaiting_card": False,
            "awaiting_relic": False,
            "awaiting_next": True,
        }
        with manager.connection() as conn:
            conn.execute(
                "INSERT INTO runs (id, party, map) VALUES (?, ?, ?)",
                (run_id, json.dumps(party_data), json.dumps(map_data)),
            )

        async def check() -> None:
            data = await get_map(run_id)
            room_data = data["current_state"]["room_data"]
            assert room_data["result"] == "boss"

        asyncio.run(check())
    finally:
        if original_db_url:
            os.environ["DATABASE_URL"] = original_db_url
        else:
            os.environ.pop("DATABASE_URL", None)
        db_path.unlink(missing_ok=True)
