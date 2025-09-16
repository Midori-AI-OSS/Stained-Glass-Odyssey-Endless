"""Async battle engine handling turn processing and rewards."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from collections.abc import Callable
import logging
import random
from typing import TYPE_CHECKING
from typing import Any

from battle_logging.writers import end_battle_logging
from services.user_level_service import gain_user_exp
from services.user_level_service import get_user_level

from autofighter.cards import card_choices
from autofighter.relics import relic_choices
from autofighter.stats import BUS
from autofighter.stats import set_enrage_percent
from autofighter.summons.base import Summon
from autofighter.summons.manager import SummonManager
from plugins.damage_types import ALL_DAMAGE_TYPES

from ...party import Party
from .events import handle_battle_end
from .events import handle_battle_start
from .pacing import _EXTRA_TURNS
from .rewards import _apply_rdr_to_stars
from .rewards import _calc_gold
from .rewards import _pick_card_stars
from .rewards import _pick_item_stars
from .rewards import _pick_relic_stars
from .rewards import _roll_relic_drop
from .setup import BattleSetupResult
from .turn_loop import run_turn_loop
from .turns import EnrageState
from .turns import build_action_queue_snapshot
from .turns import collect_summon_snapshots
from .turns import push_progress_update

if TYPE_CHECKING:
    from .core import BattleRoom


log = logging.getLogger(__name__)


ELEMENTS = [e.lower() for e in ALL_DAMAGE_TYPES]


async def run_battle(
    room: BattleRoom,
    *,
    party: Party,
    setup_data: BattleSetupResult,
    start_gold: int,
    enrage_threshold: int,
    progress: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
    run_id: str | None = None,
    battle_snapshots: dict[str, dict[str, Any]] | None = None,
    battle_tasks: dict[str, asyncio.Task[Any]] | None = None,
) -> dict[str, Any]:
    """Execute the main battle loop and return the resolution payload."""

    registry = setup_data.registry
    combat_party = setup_data.combat_party
    foes = setup_data.foes
    foe_effects = setup_data.foe_effects
    enrage_mods = setup_data.enrage_mods
    visual_queue = setup_data.visual_queue
    battle_logger = setup_data.battle_logger

    if battle_snapshots is None:
        battle_snapshots = {}
    if battle_tasks is None:
        battle_tasks = {}

    await handle_battle_start(foes, combat_party.members, registry)
    log.info(
        "Battle start: %s vs %s",
        [f.id for f in foes],
        [m.id for m in combat_party.members],
    )

    enrage_state = EnrageState(threshold=enrage_threshold)
    set_enrage_percent(0.0)

    exp_reward = 0

    def _abort(other_id: str) -> None:
        msg = "concurrent battle detected"
        snap = {
            "result": "error",
            "error": msg,
            "ended": True,
            "party": [],
            "foes": [],
            "awaiting_next": False,
            "awaiting_card": False,
            "awaiting_relic": False,
            "awaiting_loot": False,
        }
        if run_id is not None:
            battle_snapshots[run_id] = snap
        battle_snapshots[other_id] = snap
        raise RuntimeError(msg)

    temp_rdr = party.rdr
    turn, temp_rdr, exp_reward = await run_turn_loop(
        room=room,
        party=party,
        combat_party=combat_party,
        registry=registry,
        foes=foes,
        foe_effects=foe_effects,
        enrage_mods=enrage_mods,
        enrage_state=enrage_state,
        progress=progress,
        visual_queue=visual_queue,
        temp_rdr=temp_rdr,
        exp_reward=exp_reward,
        run_id=run_id,
        battle_tasks=battle_tasks,
        abort=_abort,
    )

    if progress is not None:
        try:
            await push_progress_update(
                progress,
                combat_party.members,
                foes,
                enrage_state,
                temp_rdr,
                _EXTRA_TURNS,
                active_id=None,
                ended=True,
            )
        except Exception:
            pass

    await handle_battle_end(foes, combat_party.members)

    battle_result = (
        "defeat"
        if all(member.hp <= 0 for member in combat_party.members)
        else "victory"
    )
    end_battle_logging(battle_result)

    party.members = combat_party.members
    party.gold = combat_party.gold
    party.relics = combat_party.relics
    party.cards = combat_party.cards

    if any(member.hp > 0 for member in party.members) and exp_reward > 0:
        for member in party.members:
            try:
                member.gain_exp(exp_reward)
            except Exception:
                pass
        try:
            level = get_user_level()
            await gain_user_exp(int(exp_reward / max(1, level)))
        except Exception:
            pass

    foes_data = await asyncio.to_thread(
        lambda: [_serialize(foe_obj) for foe_obj in foes]
    )

    def _apply_display_overrides(payload: dict[str, Any]) -> None:
        stacks_for_display = payload.get("stacks", 0) if payload.get("active") else 0
        for foe_obj, foe_info in zip(foes, foes_data, strict=False):
            if isinstance(foe_obj, Summon):
                continue
            try:
                base_atk = foe_obj.get_base_stat("atk")
            except Exception:
                base_atk = getattr(foe_obj, "atk", 0)
            display_base = int(round(base_atk / 20)) if base_atk else 0
            foe_info["atk"] = display_base + stacks_for_display * 2

    for mod in enrage_mods:
        if mod is not None:
            mod.remove()
    for member in combat_party.members:
        manager = member.effect_manager
        await manager.cleanup(member)
    for foe_obj, manager in zip(foes, foe_effects, strict=False):
        await manager.cleanup(foe_obj)

    try:
        set_enrage_percent(0.0)
    except Exception:
        pass

    try:
        from autofighter.stats import set_battle_active

        set_battle_active(False)
    except Exception:
        pass

    party_data = await asyncio.to_thread(
        lambda: [_serialize(member) for member in party.members]
    )
    party_summons, foe_summons = await asyncio.gather(
        collect_summon_snapshots(party.members),
        collect_summon_snapshots(foes),
    )
    action_queue_snapshot = await build_action_queue_snapshot(
        party.members,
        foes,
        _EXTRA_TURNS,
    )
    SummonManager.cleanup()

    if all(member.hp <= 0 for member in combat_party.members):
        loot = {
            "gold": 0,
            "card_choices": [],
            "relic_choices": [],
            "items": [],
        }
        enrage_payload = enrage_state.as_payload()
        if enrage_payload.get("active"):
            stacks_display = max(turn - enrage_threshold, 0)
            enrage_payload["stacks"] = stacks_display
            enrage_payload["turns"] = stacks_display
        _apply_display_overrides(enrage_payload)

        return {
            "result": "defeat",
            "party": party_data,
            "party_summons": party_summons,
            "gold": party.gold,
            "relics": party.relics,
            "cards": party.cards,
            "card_choices": [],
            "relic_choices": [],
            "loot": loot,
            "foes": [
                foe_info
                for foe_obj, foe_info in zip(foes, foes_data, strict=False)
                if not isinstance(foe_obj, Summon)
            ],
            "foe_summons": foe_summons,
            "room_number": room.node.index,
            "exp_reward": exp_reward,
            "enrage": enrage_payload,
            "rdr": temp_rdr,
            "action_queue": action_queue_snapshot,
            "ended": True,
        }

    selected_cards: list[Any] = []
    attempts = 0
    log.info(
        "Starting card selection for run %s, party has %d cards",
        getattr(combat_party, "cards", []),
        len(getattr(combat_party, "cards", [])),
    )
    while len(selected_cards) < 3 and attempts < 30:
        attempts += 1
        base_stars = _pick_card_stars(room)
        card_stars = _apply_rdr_to_stars(base_stars, temp_rdr)
        log.debug(
            "Card selection attempt %d: base_stars=%d, rdr_stars=%d",
            attempts,
            base_stars,
            card_stars,
        )
        choices = card_choices(combat_party, card_stars, count=1)
        log.debug("  card_choices returned %d options", len(choices))
        if not choices:
            log.debug("  No cards available for star level %d", card_stars)
            continue
        candidate = choices[0]
        log.debug(
            "  Candidate card: %s (%s) - %d stars",
            candidate.id,
            candidate.name,
            candidate.stars,
        )
        if any(card.id == candidate.id for card in selected_cards):
            log.debug("  Card %s already selected, skipping", candidate.id)
            continue
        selected_cards.append(candidate)
        log.debug("  Added card: %s", candidate.id)
    log.info(
        "Card selection complete: %d cards selected after %d attempts",
        len(selected_cards),
        attempts,
    )
    if selected_cards:
        log.info("Selected cards: %s", [card.id for card in selected_cards])
    else:
        log.warning("No cards were selected!")
    card_choice_data = [
        {
            "id": card.id,
            "name": card.name,
            "stars": card.stars,
            "about": card.about,
        }
        for card in selected_cards
    ]

    relic_options: list[Any] = []
    if _roll_relic_drop(room, temp_rdr):
        picked: list[Any] = []
        tries = 0
        while len(picked) < 3 and tries < 30:
            tries += 1
            relic_stars = _apply_rdr_to_stars(
                _pick_relic_stars(room),
                temp_rdr,
            )
            choices = relic_choices(combat_party, relic_stars, count=1)
            if not choices:
                continue
            relic = choices[0]
            if any(existing.id == relic.id for existing in picked):
                continue
            picked.append(relic)
        relic_options = picked

    if not selected_cards:
        from plugins.relics.fallback_essence import FallbackEssence

        fallback_relic = FallbackEssence()
        if not relic_options:
            relic_options = [fallback_relic]
        else:
            relic_options.append(fallback_relic)

    relic_choice_data = [
        {
            "id": relic.id,
            "name": relic.name,
            "stars": relic.stars,
            "about": relic.describe(party.relics.count(relic.id) + 1),
            "stacks": party.relics.count(relic.id),
        }
        for relic in relic_options
    ]

    gold_reward = _calc_gold(room, temp_rdr)
    party.gold += gold_reward
    await BUS.emit_async("gold_earned", gold_reward)

    item_base = 1 * temp_rdr
    base_int = int(item_base)
    item_count = max(1, base_int)
    if random.random() < item_base - base_int:
        item_count += 1
    items = [
        {"id": random.choice(ELEMENTS), "stars": _pick_item_stars(room)}
        for _ in range(item_count)
    ]
    ticket_chance = 0.0005 * temp_rdr
    if random.random() < ticket_chance:
        items.append({"id": "ticket", "stars": 0})

    loot = {
        "gold": party.gold - start_gold,
        "card_choices": card_choice_data,
        "relic_choices": relic_choice_data,
        "items": items,
    }
    log.info(
        "Battle rewards: gold=%s cards=%s relics=%s items=%s",
        loot["gold"],
        [choice["id"] for choice in card_choice_data],
        [choice["id"] for choice in relic_choice_data],
        items,
    )

    enrage_payload = enrage_state.as_payload()
    if enrage_payload.get("active"):
        stacks_display = max(turn - enrage_threshold, 0)
        enrage_payload["stacks"] = stacks_display
        enrage_payload["turns"] = stacks_display
    _apply_display_overrides(enrage_payload)

    return {
        "result": "boss" if room.strength > 1.0 else "battle",
        "party": party_data,
        "party_summons": party_summons,
        "gold": party.gold,
        "relics": party.relics,
        "cards": party.cards,
        "card_choices": card_choice_data,
        "relic_choices": relic_choice_data,
        "loot": loot,
        "foes": [
            foe_info
            for foe_obj, foe_info in zip(foes, foes_data, strict=False)
            if not isinstance(foe_obj, Summon)
        ],
        "foe_summons": foe_summons,
        "room_number": room.node.index,
        "battle_index": getattr(battle_logger, "battle_index", 0) if battle_logger else 0,
        "exp_reward": exp_reward,
        "enrage": enrage_payload,
        "rdr": party.rdr,
        "action_queue": action_queue_snapshot,
        "ended": True,
    }


from ..utils import _serialize  # noqa: E402  # imported late to avoid cycles

