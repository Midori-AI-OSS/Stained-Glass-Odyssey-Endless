"""Test configuration for backend suite."""

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
    writers.get_current_run_logger = lambda: BattleLogger()  # noqa: E731
    sys.modules["battle_logging.writers"] = writers
    setattr(battle_logging, "writers", writers)


def _ensure_user_level_stub() -> None:
    if "services.user_level_service" in sys.modules:
        return

    services_pkg = sys.modules.get("services")
    if services_pkg is None:
        services_pkg = types.ModuleType("services")
        sys.modules["services"] = services_pkg

    user_level = types.ModuleType("services.user_level_service")
    user_level.gain_user_exp = lambda *args, **kwargs: None  # noqa: E731
    user_level.get_user_level = lambda *args, **kwargs: 1  # noqa: E731
    sys.modules["services.user_level_service"] = user_level
    setattr(services_pkg, "user_level_service", user_level)


def _ensure_tracking_stub() -> None:
    if "tracking" in sys.modules:
        return

    tracking = types.ModuleType("tracking")
    tracking.log_battle_summary = lambda *args, **kwargs: None  # noqa: E731
    tracking.log_game_action = lambda *args, **kwargs: None  # noqa: E731
    tracking.log_play_session_end = lambda *args, **kwargs: None  # noqa: E731
    tracking.log_run_end = lambda *args, **kwargs: None  # noqa: E731
    tracking.log_menu_action = lambda *args, **kwargs: None  # noqa: E731
    tracking.log_overlay_action = lambda *args, **kwargs: None  # noqa: E731
    sys.modules["tracking"] = tracking


def _ensure_options_stub() -> None:
    if "options" in sys.modules:
        return

    options = types.ModuleType("options")

    class OptionKey(str):
        pass

    def get_option(*_args, default=None, **_kwargs):  # noqa: ANN001, D401 - simple stub
        return default

    options.OptionKey = OptionKey  # type: ignore[attr-defined]
    options.get_option = get_option  # type: ignore[attr-defined]
    sys.modules["options"] = options


def _ensure_llm_stub() -> None:
    if "llms.loader" in sys.modules:
        return

    llms = sys.modules.get("llms")
    if llms is None:
        llms = types.ModuleType("llms")
        sys.modules["llms"] = llms

    loader = types.ModuleType("llms.loader")

    class ModelName(str):
        pass

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
