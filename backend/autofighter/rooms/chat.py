from __future__ import annotations

import asyncio
from dataclasses import dataclass
import os
from typing import TYPE_CHECKING
from typing import Any

from llms.agent_loader import load_agent
from options import get_option
from tts import generate_voice

if TYPE_CHECKING:
    from midori_ai_agent_base import AgentPayload

from ..party import Party
from ..passives import PassiveRegistry
from . import Room
from .utils import _serialize


@dataclass
class ChatRoom(Room):
    """Chat rooms forward a single message to an LLM character."""

    def _build_character_context(self, member: Any) -> str:
        """Build system context for a character with their personality and appearance.

        Args:
            member: Party member with character attributes

        Returns:
            Formatted system context string
        """
        char_name = getattr(member, "name", "Unknown")
        about = getattr(member, "summarized_about", getattr(member, "full_about", ""))
        looks = getattr(member, "looks", "")

        context_parts = [f"You are {char_name}."]

        if about:
            context_parts.append(f"Here is some info about you: {about}")

        if looks:
            context_parts.append(f"This is how you look: {looks}")

        return " ".join(context_parts)

    async def resolve(self, party: Party, data: dict[str, Any]) -> dict[str, Any]:
        from midori_ai_agent_base import AgentPayload

        registry = PassiveRegistry()
        for member in party.members:
            await registry.trigger("room_enter", member)
        message = data.get("message", "")
        party_data = [_serialize(p) for p in party.members]

        # Get configuration from options
        model = get_option("lrm_model")
        backend = get_option("lrm_backend")

        # Set environment variables for API configuration if stored in options
        api_url = get_option("lrm_api_url")
        api_key = get_option("lrm_api_key")
        if api_url:
            os.environ["OPENAI_API_URL"] = api_url
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

        # Load agent using agent framework
        # Pass None for backend to let agent_loader auto-detect, or use configured backend
        agent = await load_agent(
            backend=backend if backend and backend != "auto" else None,
            model=model,
        )

        # Generate responses for each party member
        replies = []
        for member in party.members:
            # Build character-specific system context
            system_context = self._build_character_context(member)

            # Create structured payload for this member
            payload = AgentPayload(
                user_message=message,
                thinking_blob="",
                system_context=system_context,
                user_profile={},
                tools_available=[],
                session_id=f"chat-{getattr(member, 'id', 'unknown')}",
            )

            # Get response using streaming or invoke
            reply = ""
            if await agent.supports_streaming():
                async for chunk in agent.stream(payload):
                    reply += chunk
            else:
                response = await agent.invoke(payload)
                reply = response.response

            replies.append(f"{getattr(member, 'name', 'Unknown')}: {reply}")

        # Combine all replies
        combined_reply = "\n\n".join(replies)

        voice_path: str | None = None
        sample = None
        if party.members:
            sample = getattr(party.members[0], "voice_sample", None)
        audio = await asyncio.to_thread(generate_voice, combined_reply, sample)
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
            "response": combined_reply,
            "voice": voice_path,
            "party": party_data,
            "gold": party.gold,
            "relics": party.relics,
            "cards": party.cards,
            "rdr": party.rdr,
            "card": None,
            "foes": [],
        }
