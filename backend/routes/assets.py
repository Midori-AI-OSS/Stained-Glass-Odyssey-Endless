from __future__ import annotations

from pathlib import Path

from quart import Blueprint
from quart import jsonify
from quart import send_from_directory

bp = Blueprint("assets", __name__)

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


@bp.get("/assets/<path:filename>")
async def assets(filename: str):
    return await send_from_directory(ASSETS_DIR, filename)


@bp.get("/rooms/images")
async def room_images() -> tuple[str, int, dict[str, str]]:
    mapping = {
        "battle-weak": "textures/backgrounds/background_01.png",
        "battle-normal": "textures/backgrounds/background_01.png",
        "battle-prime": "textures/backgrounds/background_01.png",
        "battle-glitched": "textures/backgrounds/background_01.png",
        "battle-boss-floor": "textures/backgrounds/background_01.png",
        "shop": "textures/backgrounds/background_02.png",
        "rest": "textures/backgrounds/background_03.png",
    }
    images = {key: f"/assets/{rel}" for key, rel in mapping.items()}
    return jsonify({"images": images})
