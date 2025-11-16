import pytest

import llms.loader
import llms.safety
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
    # Mock OpenAI as not configured to use local models
    monkeypatch.setenv("OPENAI_API_URL", "unset")
    monkeypatch.setenv("OPENAI_API_KEY", "unset")
    monkeypatch.setattr(llms.safety, "model_memory_requirements", lambda name: (0, 0))
    monkeypatch.setattr(llms.safety, "ensure_ram", lambda required: None)
    monkeypatch.setattr(llms.safety, "pick_device", lambda: -1)
    def fake_pipeline(task: str, *, model: str, **kwargs: object) -> FakePipeline:
        assert model == ModelName.DEEPSEEK.value
        assert kwargs.get("device") == -1
        return FakePipeline(" ds")

    class DummyHF:
        def __init__(self, pipeline):
            self._pipeline = pipeline

        def invoke(self, text: str) -> str:
            return self._pipeline(text)[0]["generated_text"]

    monkeypatch.setattr(llms.loader, "HuggingFacePipeline", lambda *, pipeline: DummyHF(pipeline))
    monkeypatch.setattr(llms.loader, "pipeline", fake_pipeline)
    llm = load_llm(ModelName.DEEPSEEK.value)
    result = await _collect(llm)
    assert result == "hi ds"


@pytest.mark.asyncio
async def test_gemma_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    # Mock OpenAI as not configured to use local models
    monkeypatch.setenv("OPENAI_API_URL", "unset")
    monkeypatch.setenv("OPENAI_API_KEY", "unset")
    monkeypatch.setattr(llms.safety, "model_memory_requirements", lambda name: (0, 0))
    monkeypatch.setattr(llms.safety, "ensure_ram", lambda required: None)
    monkeypatch.setattr(llms.safety, "pick_device", lambda: -1)
    def fake_pipeline(task: str, *, model: str, **kwargs: object) -> FakePipeline:
        assert model == ModelName.GEMMA.value
        assert kwargs.get("device") == -1
        return FakePipeline(" gm")

    monkeypatch.setattr(llms.loader, "HuggingFacePipeline", lambda *, pipeline: DummyHF(pipeline))
    monkeypatch.setattr(llms.loader, "pipeline", fake_pipeline)
    llm = load_llm(ModelName.GEMMA.value)
    result = await _collect(llm)
    assert result == "hi gm"


@pytest.mark.asyncio
async def test_gguf_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    # Mock OpenAI as not configured to use local models
    monkeypatch.setenv("OPENAI_API_URL", "unset")
    monkeypatch.setenv("OPENAI_API_KEY", "unset")
    monkeypatch.setattr(llms.safety, "model_memory_requirements", lambda name: (0, 0))
    monkeypatch.setattr(llms.safety, "ensure_ram", lambda required: None)
    monkeypatch.setattr(llms.safety, "pick_device", lambda: -1)
    monkeypatch.setattr(llms.safety, "gguf_strategy", lambda path: {})
    monkeypatch.setattr(llms.loader, "LlamaCpp", FakeLlama)
    llm = load_llm(ModelName.GGUF.value, gguf_path="path/to/model.gguf")
    result = await _collect(llm)
    assert result == "hi llama"


class FakeChoice:
    def __init__(self, content: str) -> None:
        self.delta = type("Delta", (), {"content": content})()


class FakeChunk:
    def __init__(self, content: str) -> None:
        self.choices = [FakeChoice(content)]


class FakeAsyncOpenAI:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.chat = type("Chat", (), {"completions": self})()

    async def create(self, **kwargs: object):
        # Simulate streaming response
        async def stream():
            yield FakeChunk("remote ")
            yield FakeChunk("response")
        return stream()


@pytest.mark.asyncio
async def test_remote_openai_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test remote OpenAI loader with URL and API key set."""
    monkeypatch.setenv("OPENAI_API_URL", "https://test.api.com/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    monkeypatch.setattr(llms.loader, "_OPENAI_AVAILABLE", True)
    monkeypatch.setattr(llms.loader, "AsyncOpenAI", FakeAsyncOpenAI)

    llm = load_llm()
    result = await _collect(llm)
    assert result == "remote response"


@pytest.mark.asyncio
async def test_remote_openai_with_custom_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test remote OpenAI loader with custom model name."""
    monkeypatch.setenv("OPENAI_API_URL", "https://test.api.com/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-123")
    monkeypatch.setattr(llms.loader, "_OPENAI_AVAILABLE", True)
    monkeypatch.setattr(llms.loader, "AsyncOpenAI", FakeAsyncOpenAI)

    llm = load_llm(model="custom-model:30b")
    result = await _collect(llm)
    assert result == "remote response"


@pytest.mark.asyncio
async def test_remote_openai_not_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that local models are used when remote OpenAI is not configured."""
    monkeypatch.setenv("OPENAI_API_URL", "unset")
    monkeypatch.setenv("OPENAI_API_KEY", "unset")
    monkeypatch.setattr(llms.safety, "model_memory_requirements", lambda name: (0, 0))
    monkeypatch.setattr(llms.safety, "ensure_ram", lambda required: None)
    monkeypatch.setattr(llms.safety, "pick_device", lambda: -1)

    def fake_pipeline(task: str, *, model: str, **kwargs: object) -> FakePipeline:
        return FakePipeline(" local")

    monkeypatch.setattr(llms.loader, "HuggingFacePipeline", lambda *, pipeline: DummyHF(pipeline))
    monkeypatch.setattr(llms.loader, "pipeline", fake_pipeline)

    llm = load_llm(ModelName.DEEPSEEK.value)
    result = await _collect(llm)
    assert result == "hi local"
