from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from llms import load_agent
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
        model = await get_option("lrm_model", "openai/gpt-oss-20b")

        # Load agent (already async)
        agent = await load_agent(model=model)
        payload_data = {"party": party_data, "message": message}
        prompt_text = json.dumps(payload_data)

        # Create agent payload
        try:
            from midori_ai_agent_base import AgentPayload

            payload = AgentPayload(
                user_message=prompt_text,
                thinking_blob="",
                system_context="You are a character in the AutoFighter game chat room.",
                user_profile={},
                tools_available=[],
                session_id="chat_room",
            )

            reply = ""
            async for chunk in agent.stream(payload):
                reply += chunk
        except ImportError:
            # Fallback if agent framework not available
            reply = "Agent framework not available"

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
