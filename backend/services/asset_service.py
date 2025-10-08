"""Asset manifest helpers for the WebUI bootstrap payload."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# Canonical descriptor describing how the WebUI should alias assets that live on
# disk. The structure is intentionally lightweight so it can be serialized to
# JSON without additional processing.
_UI_ASSET_MANIFEST: dict[str, Any] = {
    "portraits": [
        {
            "id": "player",
            "folder": "characters/player",
            "aliases": [],
        },
        {
            "id": "echo",
            "folder": "characters/echo",
            "aliases": ["lady_echo"],
        },
        {
            "id": "mimic",
            "folder": None,
            "aliases": [],
            "mimic": {
                "mode": "player_mirror",
                "target": "player",
            },
        },
    ],
    "summons": [
        {
            "id": "jellyfish",
            "folder": "summons/jellyfish",
            "aliases": [
                "jellyfish_healing",
                "jellyfish_electric",
                "jellyfish_poison",
                "jellyfish_shielding",
            ],
            "portrait": True,
        },
        {
            "id": "lightstreamswords",
            "folder": "summons/lightstreamswords",
            "aliases": ["lightstreamsword"],
            "portrait": False,
        },
    ],
}


def get_asset_manifest() -> dict[str, Any]:
    """Return a deep copy of the UI asset manifest for bootstrap payloads."""

    return deepcopy(_UI_ASSET_MANIFEST)


__all__ = ["get_asset_manifest"]
