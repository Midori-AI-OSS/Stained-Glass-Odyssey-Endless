from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
from llms.loader import ModelName
from llms.loader import load_llm


class FakePipeline:
    def __init__(self, suffix: str) -> None:
        self._suffix = suffix
        self.task = "text-generation"
        self.model = type("M", (), {"name_or_path": "fake"})()

    def __call__(self, prompts: str | list[str], **_: object) -> list[dict[str, str]]:
        if isinstance(prompts, list):
            return [{"generated_text": f"{p}{self._suffix}"} for p in prompts]
        return [{"generated_text": f"{prompts}{self._suffix}"}]


class FakeLlama:
    def __init__(self, *, model_path: str) -> None:
        self._path = model_path

    def invoke(self, prompt: str) -> str:
        return f"{prompt} llama"


class DummyHF:
    def __init__(self, pipeline):
        self._pipeline = pipeline

    def invoke(self, text: str) -> str:
        return self._pipeline(text)[0]["generated_text"]


async def _collect(llm) -> str:
    chunks = [chunk async for chunk in llm.generate_stream("hi")]
    return "".join(chunks)


@pytest.mark.asyncio
async def test_deepseek_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("llms.loader._IMPORT_ERROR", None)
    monkeypatch.setattr("llms.loader.model_memory_requirements", lambda name: (0, 0))
    monkeypatch.setattr("llms.loader.ensure_ram", lambda required: None)
    monkeypatch.setattr("llms.loader.pick_device", lambda: -1)

    def fake_pipeline(task: str, *, model: str, **kwargs: object) -> FakePipeline:
        assert model == ModelName.DEEPSEEK.value
        assert kwargs.get("device") == -1
        return FakePipeline(" ds")

    class DummyHF:
        def __init__(self, pipeline):
            self._pipeline = pipeline

        def invoke(self, text: str) -> str:
            return self._pipeline(text)[0]["generated_text"]

    monkeypatch.setattr(
        "llms.loader.HuggingFacePipeline", lambda *, pipeline: DummyHF(pipeline)
    )
    monkeypatch.setattr("llms.loader.pipeline", fake_pipeline)
    llm = load_llm(ModelName.DEEPSEEK.value)
    result = await _collect(llm)
    assert result == "hi ds"


@pytest.mark.asyncio
async def test_gemma_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("llms.loader._IMPORT_ERROR", None)
    monkeypatch.setattr("llms.loader.model_memory_requirements", lambda name: (0, 0))
    monkeypatch.setattr("llms.loader.ensure_ram", lambda required: None)
    monkeypatch.setattr("llms.loader.pick_device", lambda: -1)

    def fake_pipeline(task: str, *, model: str, **kwargs: object) -> FakePipeline:
        assert model == ModelName.GEMMA.value
        assert kwargs.get("device") == -1
        return FakePipeline(" gm")

    monkeypatch.setattr(
        "llms.loader.HuggingFacePipeline", lambda *, pipeline: DummyHF(pipeline)
    )
    monkeypatch.setattr("llms.loader.pipeline", fake_pipeline)
    llm = load_llm(ModelName.GEMMA.value)
    result = await _collect(llm)
    assert result == "hi gm"


@pytest.mark.asyncio
async def test_gguf_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("llms.loader._IMPORT_ERROR", None)
    monkeypatch.setattr("llms.loader.model_memory_requirements", lambda name: (0, 0))
    monkeypatch.setattr("llms.loader.ensure_ram", lambda required: None)
    monkeypatch.setattr("llms.loader.pick_device", lambda: -1)
    monkeypatch.setattr("llms.loader.gguf_strategy", lambda path: {})
    monkeypatch.setattr("llms.loader.LlamaCpp", FakeLlama)
    llm = load_llm(ModelName.GGUF.value, gguf_path="path/to/model.gguf")
    result = await _collect(llm)
    assert result == "hi llama"
