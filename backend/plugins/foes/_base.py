from __future__ import annotations

import copy
from dataclasses import dataclass
from dataclasses import field
from dataclasses import fields
import logging

from autofighter.character import CharacterType
from autofighter.stat_effect import StatEffect
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.damage_types import random_damage_type
from plugins.damage_types._base import DamageTypeBase

# Supported foe rank values for upcoming features
SUPPORTED_RANKS = (
    "normal",
    "prime",
    "glitched prime",
    "boss",
    "glitched boss",
)

# Module-level cache to avoid repeatedly loading SentenceTransformer
_EMBEDDINGS: object | None = None

log = logging.getLogger(__name__)


class SimpleConversationMemory:
    """Lightweight, dependency-free memory used as a safe default."""

    def __init__(self) -> None:
        self._history: list[tuple[str, str]] = []

    def save_context(self, inputs: dict[str, str], outputs: dict[str, str]) -> None:
        self._history.append((inputs.get("input", ""), outputs.get("output", "")))

    def load_memory_variables(self, _: dict[str, str]) -> dict[str, str]:
        lines: list[str] = []
        for human, ai in self._history:
            if human:
                lines.append(f"Human: {human}")
            if ai:
                lines.append(f"AI: {ai}")
        return {"history": "\n".join(lines)}


@dataclass
class FoeBase(Stats):
    plugin_type = "foe"

    hp: int = 1000
    max_hp: int = 1000
    atk: int = 100
    defense: int = 50
    gold: int = 1
    char_type: CharacterType = CharacterType.C
    prompt: str = "Foe prompt placeholder"
    about: str = "Foe description placeholder"
    voice_sample: str | None = None
    voice_gender: str | None = None

    exp: int = 1
    level: int = 1
    exp_multiplier: float = 1.0
    actions_per_turn: int = 1

    crit_rate: float = 0.05
    crit_damage: float = 2
    effect_hit_rate: float = 0.01
    damage_type: DamageTypeBase = field(default_factory=random_damage_type)

    mitigation: float = 0.001
    regain: int = 1
    dodge_odds: float = 0
    effect_resistance: float = 0.05

    vitality: float = 0.001
    action_points: int = 0
    damage_taken: int = 1
    damage_dealt: int = 1
    kills: int = 1

    last_damage_taken: int = 1

    # Encounter rank indicating foe difficulty
    rank: str = "normal"

    passives: list[str] = field(default_factory=list)
    dots: list[str] = field(default_factory=list)
    hots: list[str] = field(default_factory=list)

    stat_gain_map: dict[str, str] = field(default_factory=dict)
    stat_loss_map: dict[str, str] = field(default_factory=dict)
    lrm_memory: object | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.voice_gender is None:
            self.voice_gender = {
                CharacterType.A: "male",
                CharacterType.B: "female",
                CharacterType.C: "neutral",
            }.get(self.char_type)

        super().__post_init__()

        # Use centralized torch checker instead of individual import attempts
        from llms.torch_checker import is_torch_available

        if not is_torch_available():
            # Fall back to simple in-process memory without dependencies
            self.lrm_memory = SimpleConversationMemory()
            return

        try:
            from langchain.memory import VectorStoreRetrieverMemory
            from langchain_chroma import Chroma
            from langchain_huggingface import HuggingFaceEmbeddings
        except (ImportError, ModuleNotFoundError):
            # Fallback if imports still fail despite torch being available
            self.lrm_memory = SimpleConversationMemory()
            return

        run = getattr(self, "run_id", "run")
        ident = getattr(self, "id", type(self).__name__)
        collection = f"{run}-{ident}"
        global _EMBEDDINGS
        if _EMBEDDINGS is None:
            _EMBEDDINGS = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
            )
        embeddings = _EMBEDDINGS
        try:
            store = Chroma(
                collection_name=collection,
                embedding_function=embeddings,
            )
        except Exception:
            # If vector store init fails, use simple memory
            self.lrm_memory = SimpleConversationMemory()
            return

        self.lrm_memory = VectorStoreRetrieverMemory(
            retriever=store.as_retriever()
        )

    def __deepcopy__(self, memo):  # type: ignore[override]
        """Custom deepcopy that skips copying non-serializable memory bindings."""
        cls = type(self)
        result = cls.__new__(cls)
        memo[id(self)] = result
        for f in fields(cls):
            name = f.name
            if name == "lrm_memory":
                setattr(result, name, SimpleConversationMemory())
                continue
            val = getattr(self, name)
            setattr(result, name, copy.deepcopy(val, memo))
        return result

    async def use_ultimate(self) -> bool:
        """Consume charge and emit an event when firing the ultimate."""
        if not getattr(self, "ultimate_ready", False):
            return False
        self.ultimate_charge = 0
        self.ultimate_ready = False
        await BUS.emit_async("ultimate_used", self)
        return True


    async def send_lrm_message(self, message: str) -> dict[str, object]:
        import asyncio
        from pathlib import Path

        from llms.torch_checker import is_torch_available
        from tts import generate_voice

        if not is_torch_available():
            response = ""
            self.lrm_memory.save_context({"input": message}, {"output": response})
            return {"text": response, "voice": None}

        try:
            from llms.loader import load_llm
            llm = await asyncio.to_thread(load_llm)
        except Exception:
            class _LLM:
                async def generate_stream(self, text: str):
                    yield ""

            llm = _LLM()

        context = self.lrm_memory.load_memory_variables({}).get("history", "")
        prompt = f"{context}\n{message}".strip()
        chunks: list[str] = []
        async for chunk in llm.generate_stream(prompt):
            chunks.append(chunk)
        response = "".join(chunks)

        voice_path: str | None = None
        audio = await asyncio.to_thread(
            generate_voice, response, self.voice_sample
        )
        if audio:
            voices = Path("assets/voices")
            voices.mkdir(parents=True, exist_ok=True)
            fname = f"{getattr(self, 'id', type(self).__name__)}.wav"
            (voices / fname).write_bytes(audio)
            voice_path = f"/assets/voices/{fname}"

        self.lrm_memory.save_context({"input": message}, {"output": response})
        return {"text": response, "voice": voice_path}

    async def receive_lrm_message(self, message: str) -> None:
        self.lrm_memory.save_context({"input": ""}, {"output": message})

    async def maybe_regain(self, turn: int) -> None:
        """Regain a fraction of HP every other turn."""
        if turn % 2 != 0:
            return
        bonus = max(self.regain - 100, 0) * 0.00005
        percent = (0.01 + bonus) / 100
        heal = int(self.max_hp * percent)
        log.debug(
            "%s regains %s HP on turn %s",
            getattr(self, "id", type(self).__name__),
            heal,
            turn,
        )
        await self.apply_healing(heal)

    def _on_level_up(self) -> None:
        """Apply base bonuses then boost mitigation and vitality."""
        log.info(
            "%s leveled up to %s",
            getattr(self, "id", type(self).__name__),
            self.level + 1,
        )
        super()._on_level_up()
        self.add_effect(
            StatEffect(
                name="level_up_mitigation",
                stat_modifiers={"mitigation": 0.0001},
                source="level_up",
            )
        )
        self.add_effect(
            StatEffect(
                name="level_up_vitality",
                stat_modifiers={"vitality": 0.0001},
                source="level_up",
            )
        )
