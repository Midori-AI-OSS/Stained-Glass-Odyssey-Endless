from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from llms.loader import ModelName
from llms.loader import load_llm
from options import get_option
from tts import generate_voice

from ..party import Party
from ..passives import PassiveRegistry
from . import Room
from .utils import _serialize


@dataclass
class ChatRoom(Room):
    """Chat rooms forward a single message to an LLM character."""

    async def resolve(self, party: Party, data: dict[str, Any]) -> dict[str, Any]:
        import asyncio

        registry = PassiveRegistry()
        for member in party.members:
            await registry.trigger("room_enter", member)
        message = data.get("message", "")
        party_data = [_serialize(p) for p in party.members]
        model = get_option("lrm_model", ModelName.DEEPSEEK.value)

        # Load LLM in thread pool to avoid blocking the event loop
        llm = await asyncio.to_thread(load_llm, model)
        payload = {"party": party_data, "message": message}
        prompt = json.dumps(payload)
        reply = ""
        async for chunk in llm.generate_stream(prompt):
            reply += chunk

        voice_path: str | None = None
        sample = None
        if party.members:
            sample = getattr(party.members[0], "voice_sample", None)
        audio = await asyncio.to_thread(generate_voice, reply, sample)
        if audio:
            from pathlib import Path

            voices = Path("assets/voices")
            voices.mkdir(parents=True, exist_ok=True)
            fname = "chat.wav"
            (voices / fname).write_bytes(audio)
            voice_path = f"/assets/voices/{fname}"
        return {
            "result": "chat",
            "message": message,
            "response": reply,
            "voice": voice_path,
            "party": party_data,
            "gold": party.gold,
            "relics": party.relics,
            "cards": party.cards,
            "rdr": party.rdr,
            "card": None,
            "foes": [],
        }
