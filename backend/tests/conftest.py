"""Test configuration for backend suite."""

import sys
import types


def _ensure_battle_logging_stub() -> None:
    if "battle_logging.writers" in sys.modules:
        return

    battle_logging = sys.modules.get("battle_logging")
    if battle_logging is None:
        battle_logging = types.ModuleType("battle_logging")
        sys.modules["battle_logging"] = battle_logging

    writers = types.ModuleType("battle_logging.writers")
    writers.end_battle_logging = lambda *args, **kwargs: None  # noqa: E731

    class BattleLogger:  # pragma: no cover - simple stub
        def __init__(self, *args, **kwargs) -> None:  # noqa: D401, ANN001
            return

        def start(self, *args, **kwargs) -> None:  # noqa: D401, ANN001
            return

        def stop(self, *args, **kwargs) -> None:  # noqa: D401, ANN001
            return

    class RunLogger:  # pragma: no cover - simple stub
        def __init__(self, *args, **kwargs) -> None:  # noqa: D401, ANN001
            return

        def start_battle(self, *args, **kwargs) -> BattleLogger:  # noqa: D401, ANN001
            return BattleLogger()

        def end_battle(self, *args, **kwargs) -> None:  # noqa: D401, ANN001
            return

        def finalize_run(self, *args, **kwargs) -> None:  # noqa: D401, ANN001
            return

    writers.BattleLogger = BattleLogger  # type: ignore[attr-defined]
    writers.RunLogger = RunLogger  # type: ignore[attr-defined]
    writers.start_battle_logging = lambda *args, **kwargs: BattleLogger()  # noqa: E731
    _run_state = {"current": None}

    def _start_run_logging(*args, **kwargs) -> RunLogger:  # pragma: no cover - simple stub
        logger = RunLogger(*args, **kwargs)
        _run_state["current"] = logger
        return logger

    def _get_current_run_logger() -> RunLogger | None:  # pragma: no cover - simple stub
        return _run_state.get("current")

    def _end_run_logging(*args, **kwargs) -> None:  # pragma: no cover - simple stub
        _run_state["current"] = None

    writers.get_current_run_logger = _get_current_run_logger  # type: ignore[attr-defined]
    writers.start_run_logging = _start_run_logging  # type: ignore[attr-defined]
    writers.end_run_logging = _end_run_logging  # type: ignore[attr-defined]
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
    user_level_state = {"level": 1, "exp": 0, "next_level_exp": 100}

    async def _gain_user_exp(amount: int = 0, *args, **kwargs):  # pragma: no cover - simple stub
        return dict(user_level_state)

    def _get_user_level(*args, **kwargs):  # pragma: no cover - simple stub
        return user_level_state["level"]

    def _get_user_state(*args, **kwargs):  # pragma: no cover - simple stub
        return dict(user_level_state)

    def _apply_user_level_to_party(*args, **kwargs) -> None:  # pragma: no cover - simple stub
        return

    def _user_exp_to_level(level: int) -> int:  # pragma: no cover - simple stub
        return user_level_state["next_level_exp"]

    user_level.gain_user_exp = _gain_user_exp  # type: ignore[attr-defined]
    user_level.get_user_level = _get_user_level  # type: ignore[attr-defined]
    user_level.get_user_state = _get_user_state  # type: ignore[attr-defined]
    user_level.apply_user_level_to_party = _apply_user_level_to_party  # type: ignore[attr-defined]
    user_level.user_exp_to_level = _user_exp_to_level  # type: ignore[attr-defined]
    sys.modules["services.user_level_service"] = user_level
    setattr(services_pkg, "user_level_service", user_level)


def _ensure_login_reward_stub() -> None:
    if "services.login_reward_service" in sys.modules:
        return

    services_pkg = sys.modules.get("services")
    if services_pkg is None:
        services_pkg = types.ModuleType("services")
        sys.modules["services"] = services_pkg

    login_rewards = types.ModuleType("services.login_reward_service")
    login_rewards.STATE_KEY = "login_rewards"  # type: ignore[attr-defined]
    login_rewards.ROOMS_REQUIRED = 3  # type: ignore[attr-defined]
    login_rewards.ALL_DAMAGE_TYPES = ("Light", "Fire", "Ice", "Wind", "Dark", "Lightning")  # type: ignore[attr-defined]

    async def _get_login_reward_status(*args, **kwargs):  # pragma: no cover - simple stub
        return {
            "streak": 1,
            "rooms_completed": 0,
            "rooms_required": login_rewards.ROOMS_REQUIRED,
            "claimed_today": False,
            "can_claim": False,
            "seconds_until_reset": 0,
            "reward_items": [],
            "daily_rdr_bonus": 0.0,
            "inventory": {},
        }

    async def _claim_login_reward(*args, **kwargs):  # pragma: no cover - simple stub
        return await _get_login_reward_status(*args, **kwargs)

    async def _record_room_completion(*args, **kwargs):  # pragma: no cover - simple stub
        return None

    async def _get_daily_rdr_bonus(*args, **kwargs):  # pragma: no cover - simple stub
        return 0.0

    login_rewards.get_login_reward_status = _get_login_reward_status  # type: ignore[attr-defined]
    login_rewards.claim_login_reward = _claim_login_reward  # type: ignore[attr-defined]
    login_rewards.record_room_completion = _record_room_completion  # type: ignore[attr-defined]
    login_rewards.get_daily_rdr_bonus = _get_daily_rdr_bonus  # type: ignore[attr-defined]

    sys.modules["services.login_reward_service"] = login_rewards
    setattr(services_pkg, "login_reward_service", login_rewards)


def _ensure_reward_service_stub() -> None:
    if "services.reward_service" in sys.modules:
        return

    services_pkg = sys.modules.get("services")
    if services_pkg is None:
        services_pkg = types.ModuleType("services")
        sys.modules["services"] = services_pkg

    reward_service = types.ModuleType("services.reward_service")

    async def _select_card(*args, **kwargs):  # pragma: no cover - simple stub
        return {"card": None, "cards": []}

    async def _select_relic(*args, **kwargs):  # pragma: no cover - simple stub
        return {"relic": None, "relics": []}

    async def _acknowledge_loot(*args, **kwargs):  # pragma: no cover - simple stub
        return {"next_room": None}

    reward_service.select_card = _select_card  # type: ignore[attr-defined]
    reward_service.select_relic = _select_relic  # type: ignore[attr-defined]
    reward_service.acknowledge_loot = _acknowledge_loot  # type: ignore[attr-defined]

    sys.modules["services.reward_service"] = reward_service
    setattr(services_pkg, "reward_service", reward_service)


def _ensure_run_service_stub() -> None:
    if "services.run_service" in sys.modules:
        return

    services_pkg = sys.modules.get("services")
    if services_pkg is None:
        services_pkg = types.ModuleType("services")
        sys.modules["services"] = services_pkg

    run_service = types.ModuleType("services.run_service")

    async def start_run(*args, **kwargs):  # pragma: no cover - simple stub
        return {"run_id": "stub-run", "party": {}, "map": {}}

    async def advance_room(*args, **kwargs):  # pragma: no cover - simple stub
        return {"room": None, "result": None}

    async def get_battle_events(*args, **kwargs):  # pragma: no cover - simple stub
        return []

    async def get_battle_summary(*args, **kwargs):  # pragma: no cover - simple stub
        return {"summary": None}

    async def restore_save(*args, **kwargs):  # pragma: no cover - simple stub
        return {"restored": False}

    async def backup_save(*args, **kwargs):  # pragma: no cover - simple stub
        return None

    async def wipe_save(*args, **kwargs):  # pragma: no cover - simple stub
        return {"status": "wiped"}

    async def get_map(*args, **kwargs):  # pragma: no cover - simple stub
        return {"rooms": [], "current": 0}

    def _choose_foe(*args, **kwargs):  # pragma: no cover - simple stub
        return None

    run_service.start_run = start_run  # type: ignore[attr-defined]
    run_service.advance_room = advance_room  # type: ignore[attr-defined]
    run_service.get_battle_events = get_battle_events  # type: ignore[attr-defined]
    run_service.get_battle_summary = get_battle_summary  # type: ignore[attr-defined]
    run_service.restore_save = restore_save  # type: ignore[attr-defined]
    run_service.backup_save = backup_save  # type: ignore[attr-defined]
    run_service.wipe_save = wipe_save  # type: ignore[attr-defined]
    run_service.get_map = get_map  # type: ignore[attr-defined]
    run_service._choose_foe = _choose_foe  # type: ignore[attr-defined]

    sys.modules["services.run_service"] = run_service
    setattr(services_pkg, "run_service", run_service)


def _ensure_room_service_stub() -> None:
    if "services.room_service" in sys.modules:
        return

    services_pkg = sys.modules.get("services")
    if services_pkg is None:
        services_pkg = types.ModuleType("services")
        sys.modules["services"] = services_pkg

    room_service = types.ModuleType("services.room_service")

    async def _battle_room(*args, **kwargs):  # pragma: no cover - simple stub
        return {"next_room": None, "result": None}

    async def _boss_room(*args, **kwargs):  # pragma: no cover - simple stub
        return {"next_room": None, "result": None}

    async def _shop_room(*args, **kwargs):  # pragma: no cover - simple stub
        return {"purchases": []}

    async def room_action(*args, **kwargs):  # pragma: no cover - simple stub
        return {"status": "ok", "result": None}

    def _collect_summons(*args, **kwargs):  # pragma: no cover - simple stub
        return []

    def _choose_foe(*args, **kwargs):  # pragma: no cover - simple stub
        return None

    def _build_foes(*args, **kwargs):  # pragma: no cover - simple stub
        return []

    async def _run_battle(*args, **kwargs):  # pragma: no cover - simple stub
        return {"outcome": None}

    def _scale_stats(*args, **kwargs):  # pragma: no cover - simple stub
        return None

    def get_room(*args, **kwargs):  # pragma: no cover - simple stub
        return None

    room_service.battle_room = _battle_room  # type: ignore[attr-defined]
    room_service.boss_room = _boss_room  # type: ignore[attr-defined]
    room_service.shop_room = _shop_room  # type: ignore[attr-defined]
    room_service.room_action = room_action  # type: ignore[attr-defined]
    room_service._collect_summons = _collect_summons  # type: ignore[attr-defined]
    room_service._choose_foe = _choose_foe  # type: ignore[attr-defined]
    room_service._build_foes = _build_foes  # type: ignore[attr-defined]
    room_service._run_battle = _run_battle  # type: ignore[attr-defined]
    room_service._scale_stats = _scale_stats  # type: ignore[attr-defined]
    room_service.get_room = get_room  # type: ignore[attr-defined]

    sys.modules["services.room_service"] = room_service
    setattr(services_pkg, "room_service", room_service)


def _ensure_tracking_stub() -> None:
    if "tracking" in sys.modules:
        return

    tracking = types.ModuleType("tracking")
    tracking.get_tracking_manager = lambda *args, **kwargs: None  # noqa: E731

    def _noop(*args, **kwargs):  # pragma: no cover - simple stub
        return None

    _tracking_calls = {
        "log_achievement_unlock",
        "log_battle_summary",
        "log_card_acquisition",
        "log_character_pull",
        "log_deck_change",
        "log_event_choice",
        "log_game_action",
        "log_login_event",
        "log_menu_action",
        "log_overlay_action",
        "log_play_session_end",
        "log_play_session_start",
        "log_relic_acquisition",
        "log_run_end",
        "log_run_start",
        "log_settings_change",
        "log_shop_transaction",
    }

    for _name in _tracking_calls:
        setattr(tracking, _name, _noop)
    sys.modules["tracking"] = tracking


def _ensure_options_stub() -> None:
    if "options" in sys.modules:
        return

    options = types.ModuleType("options")

    class OptionKey(str):
        pass

    _store: dict[str, object] = {}

    def set_option(key: OptionKey | str, value: object) -> None:  # pragma: no cover - simple stub
        _store[str(key)] = value

    def get_option(  # pragma: no cover - simple stub
        key: OptionKey | str | None = None,
        *_,
        default: object | None = None,
        **__,
    ) -> object | None:
        if key is None:
            return default
        return _store.get(str(key), default)

    options.OptionKey = OptionKey  # type: ignore[attr-defined]
    options.get_option = get_option  # type: ignore[attr-defined]
    options.set_option = set_option  # type: ignore[attr-defined]
    sys.modules["options"] = options


def _ensure_llm_stub() -> None:
    if "llms.loader" in sys.modules and "llms.torch_checker" in sys.modules:
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

    def _is_torch_available() -> bool:  # pragma: no cover - simple stub
        return False

    def _get_torch_import_error() -> None:  # pragma: no cover - simple stub
        return None

    def _require_torch() -> None:  # pragma: no cover - simple stub
        msg = "Torch dependencies are not available in the test environment."
        raise RuntimeError(msg)

    torch_checker.is_torch_available = _is_torch_available  # type: ignore[attr-defined]
    torch_checker.get_torch_import_error = _get_torch_import_error  # type: ignore[attr-defined]
    torch_checker.require_torch = _require_torch  # type: ignore[attr-defined]
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
_ensure_login_reward_stub()
_ensure_reward_service_stub()
_ensure_run_service_stub()
_ensure_room_service_stub()
_ensure_tracking_stub()
_ensure_options_stub()
_ensure_llm_stub()
_ensure_tts_stub()
