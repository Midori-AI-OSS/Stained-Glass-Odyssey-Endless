"""Test configuration for backend suite."""

from enum import Enum
from pathlib import Path
import sys
import types

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def _ensure_battle_logging_stub() -> None:
    if "battle_logging.writers" in sys.modules:
        return

    battle_logging = sys.modules.get("battle_logging")
    if battle_logging is None:
        battle_logging = types.ModuleType("battle_logging")
        sys.modules["battle_logging"] = battle_logging

    writers = types.ModuleType("battle_logging.writers")
    writers.end_battle_logging = lambda *args, **kwargs: None  # noqa: E731
    writers.end_run_logging = lambda *args, **kwargs: None  # noqa: E731

    class BattleLogger:  # pragma: no cover - simple stub
        def __init__(self, *args, **kwargs) -> None:  # noqa: D401, ANN001
            return

        def start(self, *args, **kwargs) -> None:  # noqa: D401, ANN001
            return

        def stop(self, *args, **kwargs) -> None:  # noqa: D401, ANN001
            return

    writers.BattleLogger = BattleLogger  # type: ignore[attr-defined]
    writers.start_battle_logging = lambda *args, **kwargs: BattleLogger()  # noqa: E731
    writers.start_run_logging = lambda *args, **kwargs: None  # noqa: E731
    writers.get_current_run_logger = lambda: BattleLogger()  # noqa: E731
    sys.modules["battle_logging.writers"] = writers
    setattr(battle_logging, "writers", writers)


def _ensure_user_level_stub() -> None:
    if "services.user_level_service" in sys.modules:
        return

    services_pkg = sys.modules.get("services")
    services_path = str(Path(__file__).resolve().parents[1] / "services")

    if services_pkg is None:
        services_pkg = types.ModuleType("services")
        services_pkg.__path__ = [services_path]  # type: ignore[attr-defined]
        sys.modules["services"] = services_pkg
    else:
        existing = getattr(services_pkg, "__path__", [])
        if not existing:
            services_pkg.__path__ = [services_path]  # type: ignore[attr-defined]

    user_level = types.ModuleType("services.user_level_service")
    user_level.gain_user_exp = lambda *args, **kwargs: None  # noqa: E731
    user_level.get_user_level = lambda *args, **kwargs: 1  # noqa: E731
    user_level.get_user_state = lambda *args, **kwargs: {"level": 1, "exp": 0}  # noqa: E731
    sys.modules["services.user_level_service"] = user_level
    setattr(services_pkg, "user_level_service", user_level)


def _ensure_tracking_stub() -> None:
    if "tracking" in sys.modules:
        return

    tracking = types.ModuleType("tracking")

    async def _async_noop(*_args, **_kwargs):  # noqa: ANN001, D401
        return None

    tracking.log_battle_summary = _async_noop
    tracking.log_card_acquisition = _async_noop
    tracking.log_deck_change = _async_noop
    tracking.log_game_action = _async_noop
    tracking.log_character_pull = _async_noop
    tracking.log_event_choice = _async_noop
    tracking.log_login_event = _async_noop
    tracking.log_shop_transaction = _async_noop
    tracking.log_play_session_end = _async_noop
    tracking.log_play_session_start = _async_noop
    tracking.log_run_end = _async_noop
    tracking.log_run_start = _async_noop
    tracking.log_menu_action = _async_noop
    tracking.log_overlay_action = _async_noop
    tracking.log_settings_change = _async_noop
    tracking.log_relic_acquisition = _async_noop
    sys.modules["tracking"] = tracking

    class _TrackingConnection:
        def __enter__(self):  # noqa: D401
            return self

        def __exit__(self, exc_type, exc, tb):  # noqa: D401, ANN001
            return False

        def execute(self, *_args, **_kwargs):  # noqa: ANN002, D401
            class _Cursor:
                description: list[tuple[str, ...]] = []

                def fetchall(self):  # noqa: D401
                    return []

                def fetchone(self):  # noqa: D401
                    return (0,)

            return _Cursor()

    class _TrackingManager:
        def connection(self):  # noqa: D401
            return _TrackingConnection()

    tracking.get_tracking_manager = lambda: _TrackingManager()  # noqa: E731


def _ensure_options_stub() -> None:
    if "options" in sys.modules:
        return

    options = types.ModuleType("options")

    class OptionKey(str):
        """Lightweight stand-in for :class:`backend.options.OptionKey`."""

        def __new__(cls, value: str):  # noqa: D401
            return str.__new__(cls, value)


    OptionKey.LRM_MODEL = OptionKey("lrm_model")
    OptionKey.TURN_PACING = OptionKey("turn_pacing")

    _store: dict[str, str] = {}

    def get_option(key, default=None):  # noqa: ANN001, D401 - simple stub
        return _store.get(str(key), default)

    def set_option(key, value):  # noqa: ANN001, D401 - simple stub
        _store[str(key)] = value
        return None

    options.OptionKey = OptionKey  # type: ignore[attr-defined]
    options.get_option = get_option  # type: ignore[attr-defined]
    options.set_option = set_option  # type: ignore[attr-defined]
    sys.modules["options"] = options


def _ensure_llm_stub() -> None:
    if "llms.loader" in sys.modules:
        return

    llms = sys.modules.get("llms")
    if llms is None:
        llms = types.ModuleType("llms")
        sys.modules["llms"] = llms

    loader = types.ModuleType("llms.loader")

    class ModelName(str, Enum):
        DEEPSEEK = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
        GEMMA = "google/gemma-3-4b-it"
        GGUF = "gguf"

    loader.ModelName = ModelName  # type: ignore[attr-defined]
    loader.pipeline = lambda *args, **kwargs: None  # noqa: E731
    loader.load_llm = lambda *args, **kwargs: None  # noqa: E731
    sys.modules["llms.loader"] = loader
    setattr(llms, "loader", loader)

    torch_checker = types.ModuleType("llms.torch_checker")
    torch_checker.is_torch_available = lambda: False  # noqa: E731
    torch_checker.get_torch_import_error = lambda: "missing"  # noqa: E731
    torch_checker.require_torch = lambda: None  # noqa: E731
    sys.modules["llms.torch_checker"] = torch_checker
    setattr(llms, "torch_checker", torch_checker)


def _ensure_tts_stub() -> None:
    if "tts" in sys.modules:
        return

    tts = types.ModuleType("tts")
    tts.generate_voice = lambda *args, **kwargs: None  # noqa: E731
    sys.modules["tts"] = tts


_ensure_battle_logging_stub()
_ensure_user_level_stub()
_ensure_tracking_stub()
_ensure_options_stub()
_ensure_llm_stub()
_ensure_tts_stub()


def _ensure_runs_module() -> None:
    if "runs" in sys.modules:
        return

    import importlib

    importlib.import_module("runs")


_ensure_runs_module()
