"""Test configuration for backend suite."""

import asyncio
import copy
import json
import os
from pathlib import Path
import sys
import types

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.mapgen import MapNode


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


def _ensure_rich_stub() -> None:
    if "rich.console" in sys.modules:
        return

    rich = sys.modules.get("rich")
    if rich is None:
        rich = types.ModuleType("rich")
        rich.__path__ = []  # type: ignore[attr-defined]
        sys.modules["rich"] = rich

    console = types.ModuleType("rich.console")

    class _Console:
        def print(self, *_args, **_kwargs):  # noqa: ANN002, D401
            return None

        def log(self, *_args, **_kwargs):  # noqa: ANN002, D401
            return None

    console.Console = _Console  # type: ignore[attr-defined]
    sys.modules["rich.console"] = console
    setattr(rich, "console", console)

    logging_module = types.ModuleType("rich.logging")

    class _RichHandler:
        def __init__(self, *_args, **_kwargs):  # noqa: ANN002, D401
            self.level = 0

        def setFormatter(self, *_args, **_kwargs):  # noqa: ANN002, D401, N802
            return None

        def setLevel(self, level):  # noqa: D401, ANN001
            self.level = level

        def handle(self, _record):  # noqa: D401, ANN001
            return None

        def emit(self, _record):  # noqa: D401, ANN001
            return None

    logging_module.RichHandler = _RichHandler  # type: ignore[attr-defined]
    sys.modules["rich.logging"] = logging_module
    setattr(rich, "logging", logging_module)


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
    # Try to import the real llms package first
    try:
        import llms
        import llms.loader
        import llms.torch_checker
        # Real package exists, don't stub it
        return
    except ImportError:
        pass

    if "llms.loader" in sys.modules:
        return

    llms = sys.modules.get("llms")
    if llms is None:
        llms = types.ModuleType("llms")
        sys.modules["llms"] = llms

    # Mock load_agent instead of load_llm
    llms.load_agent = lambda *args, **kwargs: None  # noqa: E731
    llms.validate_agent = lambda *args, **kwargs: True  # noqa: E731
    llms.get_agent_config = lambda *args, **kwargs: None  # noqa: E731

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
_ensure_rich_stub()
_ensure_options_stub()
_ensure_llm_stub()
_ensure_tts_stub()


def _ensure_runs_module() -> None:
    if "runs" in sys.modules:
        return

    runs = types.ModuleType("runs")
    sys.modules["runs"] = runs

    encryption = types.ModuleType("runs.encryption")

    class _DummyFernet:
        def encrypt(self, data):  # noqa: D401, ANN001
            return data

        def decrypt(self, token):  # noqa: D401, ANN001
            return token

    class _Cursor:
        def __init__(self, rows):  # noqa: ANN001, D401
            self._rows = rows
            self.description = []

        def fetchone(self):  # noqa: D401
            return self._rows[0] if self._rows else None

        def fetchall(self):  # noqa: D401
            return list(self._rows)

    _RUN_ROWS: dict[str, dict[str, str]] = {}
    _OWNED_PLAYERS: set[str] = {"player"}
    _DAMAGE_TYPES: dict[str, str] = {}

    class _SaveConnection:
        def __enter__(self):  # noqa: D401
            return self

        def __exit__(self, exc_type, exc, tb):  # noqa: D401, ANN001
            return False

        def execute(self, query, params=()):  # noqa: ANN001, D401
            normalized = " ".join(str(query).strip().split()).lower()
            args: tuple = ()
            if isinstance(params, (list, tuple)):
                args = tuple(params)
            elif params is not None:
                args = (params,)

            if normalized.startswith("pragma") or normalized.startswith("create table"):
                return _Cursor([])

            if normalized.startswith("insert into runs"):
                run_id, party_blob, map_blob = args
                _RUN_ROWS[str(run_id)] = {
                    "party": party_blob,
                    "map": map_blob,
                }
                return _Cursor([])

            if normalized.startswith("update runs set map"):
                map_blob, run_id = args
                entry = _RUN_ROWS.setdefault(str(run_id), {"party": json.dumps({}), "map": json.dumps({})})
                entry["map"] = map_blob
                return _Cursor([])

            if normalized.startswith("select party from runs where id"):
                run_id = str(args[0])
                entry = _RUN_ROWS.get(run_id)
                return _Cursor([(entry["party"],)] if entry else [])

            if normalized.startswith("select map from runs where id"):
                run_id = str(args[0])
                entry = _RUN_ROWS.get(run_id)
                return _Cursor([(entry["map"],)] if entry else [])

            if normalized.startswith("select id, party, map from runs"):
                rows = [(rid, data.get("party"), data.get("map")) for rid, data in _RUN_ROWS.items()]
                return _Cursor(rows)

            if normalized.startswith("select id from runs"):
                rows = [(rid,) for rid in _RUN_ROWS]
                return _Cursor(rows)

            if normalized.startswith("delete from runs where id"):
                run_id = str(args[0])
                _RUN_ROWS.pop(run_id, None)
                return _Cursor([])

            if normalized.startswith("delete from runs"):
                _RUN_ROWS.clear()
                return _Cursor([])

            if normalized.startswith("select count(*) from owned_players"):
                return _Cursor([(len(_OWNED_PLAYERS),)])

            if normalized.startswith("insert into owned_players"):
                if args:
                    _OWNED_PLAYERS.add(str(args[0]))
                return _Cursor([])

            if normalized.startswith("select type from damage_types where id"):
                run_id = str(args[0])
                if run_id in _DAMAGE_TYPES:
                    return _Cursor([(_DAMAGE_TYPES[run_id],)])
                return _Cursor([])

            return _Cursor([])

    class _SaveManager:
        def connection(self):  # noqa: D401
            return _SaveConnection()

        @property
        def db_path(self):  # noqa: D401
            return os.environ.get("AF_DB_PATH", ":memory:")

        @property
        def key(self):  # noqa: D401
            return os.environ.get("AF_DB_KEY")

    encryption.get_fernet = lambda *_args, **_kwargs: _DummyFernet()  # noqa: E731
    encryption.get_save_manager = lambda *_args, **_kwargs: _SaveManager()  # noqa: E731
    sys.modules["runs.encryption"] = encryption
    setattr(runs, "encryption", encryption)

    lifecycle = types.ModuleType("runs.lifecycle")

    async def _noop_async(*_args, **_kwargs):  # noqa: ANN001, D401
        return None

    def _noop_sync(*_args, **_kwargs):  # noqa: ANN001, D401
        return None

    lifecycle._run_battle = _noop_async  # type: ignore[attr-defined]
    lifecycle.battle_snapshots = {}
    lifecycle.battle_tasks = {}
    lifecycle.battle_locks = {}
    lifecycle.reward_locks = {}
    lifecycle.REWARD_STEP_DROPS = "drops"
    lifecycle.REWARD_STEP_CARDS = "cards"
    lifecycle.REWARD_STEP_RELICS = "relics"
    lifecycle.REWARD_STEP_BATTLE_REVIEW = "battle_review"
    lifecycle.REWARD_PROGRESSION_SEQUENCE = (
        lifecycle.REWARD_STEP_DROPS,
        lifecycle.REWARD_STEP_CARDS,
        lifecycle.REWARD_STEP_RELICS,
        lifecycle.REWARD_STEP_BATTLE_REVIEW,
    )

    def _empty_reward_staging():  # noqa: D401
        return {
            "cards": [],
            "relics": [],
            "items": [],
        }

    def _ensure_reward_staging(state):  # noqa: ANN001, D401
        if not isinstance(state, dict):
            raise TypeError("state must be a dict")

        staging = state.get("reward_staging")
        changed = False
        if not isinstance(staging, dict):
            staging = {}
            changed = True

        for key in ("cards", "relics", "items"):
            value = staging.get(key)
            if isinstance(value, list):
                staging[key] = list(value)
            else:
                staging[key] = []
                changed = True

        state["reward_staging"] = staging
        return staging, changed

    def _ensure_reward_progression(state):  # noqa: ANN001, D401
        if not isinstance(state, dict):
            raise TypeError("state must be a dict")

        _, changed = _ensure_reward_staging(state)
        progression = state.get("reward_progression")
        if not isinstance(progression, dict):
            progression = {
                "available": [],
                "completed": [],
                "current": None,
            }
            changed = True
        else:
            available = progression.get("available")
            if isinstance(available, list):
                progression["available"] = list(available)
            else:
                progression["available"] = []
                changed = True

            completed = progression.get("completed")
            if isinstance(completed, list):
                progression["completed"] = list(completed)
            else:
                progression["completed"] = []
                changed = True

            current = progression.get("current")
            if current is None:
                progression["current"] = None
            else:
                progression["current"] = str(current)

        state["reward_progression"] = progression
        return progression, changed

    def _normalise_reward_step(value):  # noqa: ANN001, D401
        if value is None:
            return None
        candidate = str(value).strip().lower()
        if not candidate:
            return None
        return candidate

    def _no_pending_rewards(state=None):  # noqa: ANN001, D401
        if isinstance(state, dict):
            staging = state.get("reward_staging")
            if isinstance(staging, dict):
                return any(bool(staging.get(key)) for key in ("cards", "relics", "items"))
        return False

    def _load_map(run_id):  # noqa: ANN001, D401
        entry = _RUN_ROWS.get(str(run_id))
        if entry is None or not entry.get("map"):
            default_state: dict[str, object] = {"rooms": [], "current": 0, "battle": False}
            _ensure_reward_staging(default_state)
            _ensure_reward_progression(default_state)
            return default_state, []

        raw_state = entry.get("map")
        if isinstance(raw_state, str):
            try:
                state = json.loads(raw_state)
            except Exception:
                state = {}
        elif isinstance(raw_state, dict):
            state = copy.deepcopy(raw_state)
        else:
            state = {}

        staging, staging_changed = _ensure_reward_staging(state)
        progression, progression_changed = _ensure_reward_progression(state)

        rooms: list[MapNode] = []
        for raw in state.get("rooms", []):
            if isinstance(raw, dict):
                try:
                    rooms.append(MapNode.from_dict(raw))
                except Exception:
                    continue

        if staging_changed or progression_changed:
            entry["map"] = json.dumps(state)

        return state, rooms

    def _save_map(run_id, state):  # noqa: ANN001, D401
        if not isinstance(state, dict):
            raise TypeError("state must be a dict")
        _ensure_reward_staging(state)
        _ensure_reward_progression(state)
        entry = _RUN_ROWS.setdefault(str(run_id), {"party": json.dumps({}), "map": json.dumps({})})
        entry["map"] = json.dumps(state)
        return None

    async def _cleanup_battle_state() -> None:  # noqa: D401
        stale_runs = [run_id for run_id, task in lifecycle.battle_tasks.items() if getattr(task, "done", lambda: True)()]
        for run_id in stale_runs:
            lifecycle.battle_tasks.pop(run_id, None)
            lifecycle.battle_snapshots.pop(run_id, None)
            lifecycle.battle_locks.pop(run_id, None)
            lifecycle.reward_locks.pop(run_id, None)
        return None

    def _purge_run_state(run_id: str, *, cancel_task: bool = True) -> None:  # noqa: D401
        task = lifecycle.battle_tasks.pop(run_id, None)
        if cancel_task and task is not None and hasattr(task, "cancel"):
            task.cancel()
        lifecycle.battle_snapshots.pop(run_id, None)
        lifecycle.battle_locks.pop(run_id, None)
        lifecycle.reward_locks.pop(run_id, None)

    def _purge_all_run_state(*, cancel_tasks: bool = True) -> None:  # noqa: D401
        if cancel_tasks:
            for task in lifecycle.battle_tasks.values():
                if hasattr(task, "cancel"):
                    task.cancel()
        lifecycle.battle_tasks.clear()
        lifecycle.battle_snapshots.clear()
        lifecycle.battle_locks.clear()
        lifecycle.reward_locks.clear()

    lifecycle.empty_reward_staging = _empty_reward_staging  # type: ignore[attr-defined]
    lifecycle.ensure_reward_staging = _ensure_reward_staging  # type: ignore[attr-defined]
    lifecycle.ensure_reward_progression = _ensure_reward_progression  # type: ignore[attr-defined]
    lifecycle.normalise_reward_step = _normalise_reward_step  # type: ignore[attr-defined]
    lifecycle.has_pending_rewards = _no_pending_rewards  # type: ignore[attr-defined]
    lifecycle.cleanup_battle_state = _cleanup_battle_state  # type: ignore[attr-defined]
    lifecycle.purge_all_run_state = _purge_all_run_state  # type: ignore[attr-defined]
    lifecycle.purge_run_state = _purge_run_state  # type: ignore[attr-defined]
    lifecycle.load_map = _load_map  # type: ignore[attr-defined]
    lifecycle.save_map = _save_map  # type: ignore[attr-defined]
    lifecycle.emit_battle_end_for_runs = _noop_async  # type: ignore[attr-defined]
    lifecycle.get_battle_state_sizes = lambda: {  # noqa: E731
        "tasks": len(lifecycle.battle_tasks),
        "snapshots": len(lifecycle.battle_snapshots),
        "locks": len(lifecycle.battle_locks),
        "reward_locks": len(lifecycle.reward_locks),
    }
    sys.modules["runs.lifecycle"] = lifecycle
    setattr(runs, "lifecycle", lifecycle)

    def _load_party(run_id: str):  # noqa: D401
        entry = _RUN_ROWS.get(str(run_id))
        payload: dict[str, object]
        raw_party = entry.get("party") if entry else None
        if isinstance(raw_party, str):
            try:
                payload = json.loads(raw_party)
            except Exception:
                payload = {}
        elif isinstance(raw_party, dict):
            payload = copy.deepcopy(raw_party)
        else:
            payload = {}

        member_ids = [str(mid) for mid in payload.get("members", []) if mid]
        exp_map = payload.get("exp_multiplier", {}) if isinstance(payload.get("exp_multiplier"), dict) else {}
        members: list[types.SimpleNamespace] = []
        for mid in member_ids:
            member = types.SimpleNamespace(
                id=mid,
                name=mid,
                exp_multiplier=float(exp_map.get(mid, 1.0) or 1.0),
            )
            members.append(member)

        party = types.SimpleNamespace(
            members=members,
            gold=int(payload.get("gold", 0) or 0),
            relics=list(payload.get("relics", [])) if isinstance(payload.get("relics"), list) else [],
            cards=list(payload.get("cards", [])) if isinstance(payload.get("cards"), list) else [],
            rdr=float(payload.get("rdr", 1.0) or 1.0),
        )
        party.no_shops = bool(payload.get("no_shops", False))
        party.no_rests = bool(payload.get("no_rests", False))
        party.pull_tokens = int(payload.get("pull_tokens", 0) or 0)
        return party

    def _save_party(run_id: str, party):  # noqa: ANN001, D401
        member_ids: list[str] = []
        exp_multiplier: dict[str, float] = {}
        for member in getattr(party, "members", []) or []:
            mid = getattr(member, "id", None)
            if not mid:
                continue
            member_ids.append(str(mid))
            exp_multiplier[str(mid)] = float(getattr(member, "exp_multiplier", 1.0) or 1.0)

        payload = {
            "members": member_ids,
            "gold": int(getattr(party, "gold", 0) or 0),
            "relics": list(getattr(party, "relics", []) or []),
            "cards": list(getattr(party, "cards", []) or []),
            "exp": {mid: 0 for mid in member_ids},
            "level": {mid: 1 for mid in member_ids},
            "exp_multiplier": exp_multiplier,
            "rdr": float(getattr(party, "rdr", 1.0) or 1.0),
            "no_shops": bool(getattr(party, "no_shops", False)),
            "no_rests": bool(getattr(party, "no_rests", False)),
            "pull_tokens": int(getattr(party, "pull_tokens", 0) or 0),
        }

        entry = _RUN_ROWS.setdefault(str(run_id), {"party": json.dumps(payload), "map": json.dumps({})})
        entry["party"] = json.dumps(payload)
        return None

    party_manager = types.ModuleType("runs.party_manager")
    party_manager._apply_player_customization = _noop_sync  # type: ignore[attr-defined]
    party_manager._apply_character_customization = _noop_sync  # type: ignore[attr-defined]
    party_manager._assign_damage_type = _noop_sync  # type: ignore[attr-defined]
    party_manager._apply_player_upgrades = _noop_sync  # type: ignore[attr-defined]
    party_manager._describe_passives = _noop_sync  # type: ignore[attr-defined]
    party_manager._load_player_customization = lambda: ("", {})  # noqa: E731
    party_manager._load_character_customization = lambda *_args, **_kwargs: {}  # noqa: E731
    party_manager._load_individual_stat_upgrades = lambda *_args, **_kwargs: {}  # noqa: E731
    party_manager.load_party = _load_party  # type: ignore[attr-defined]
    party_manager.save_party = _save_party  # type: ignore[attr-defined]
    sys.modules["runs.party_manager"] = party_manager
    setattr(runs, "party_manager", party_manager)



_ensure_runs_module()


def pytest_configure(config):  # noqa: D401
    config.addinivalue_line("markers", "asyncio: mark test as running in asyncio loop")
    config.addinivalue_line("markers", "stress: mark test as stress test (run manually, not in CI)")
    config.addinivalue_line("markers", "llm_real: mark test as requiring real LLM dependencies and inference")
    config.addinivalue_line("markers", "slow: mark test as slow running (>10 seconds)")


def pytest_pyfunc_call(pyfuncitem):  # noqa: D401
    if asyncio.iscoroutinefunction(pyfuncitem.obj):
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(pyfuncitem.obj(**pyfuncitem.funcargs))
        finally:
            loop.close()
        return True
    return None
