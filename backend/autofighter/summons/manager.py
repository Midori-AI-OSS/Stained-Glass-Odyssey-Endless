from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import Dict
from typing import List
from typing import Optional

from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.damage_types._base import DamageTypeBase

from .base import Summon

log = logging.getLogger(__name__)

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from autofighter.party import Party


class SummonManager:
    """Track and control active summons."""

    _active_summons: ClassVar[Dict[str, List[Summon]]] = {}
    _summoner_refs: ClassVar[Dict[str, Stats]] = {}
    _instance_counters: ClassVar[Dict[str, int]] = {}
    _initialized: ClassVar[bool] = False

    @classmethod
    def initialize(cls) -> None:
        """Register event handlers once."""
        if cls._initialized:
            return
        BUS.subscribe("battle_start", cls._on_battle_start)
        BUS.subscribe("battle_end", cls._on_battle_end)
        BUS.subscribe("turn_start", cls._on_turn_start)
        BUS.subscribe("entity_defeat", cls._on_entity_defeat)
        BUS.subscribe("entity_killed", cls._on_entity_killed)
        cls._initialized = True
        log.debug("SummonManager initialized")

    @classmethod
    async def create_summon(
        cls,
        summoner: Stats,
        summon_type: str = "generic",
        source: str = "unknown",
        stat_multiplier: float = 0.5,
        turns_remaining: int = -1,
        override_damage_type: Optional[DamageTypeBase] = None,
        max_summons: Optional[int] = None,
        force_create: bool = False,
        min_health_threshold: float = 0.25,
    ) -> Optional[Summon]:
        cls.initialize()

        if isinstance(summoner, Summon):
            log.warning(
                "Summon %s attempted to create another summon - blocked for safety",
                getattr(summoner, "id", "unknown"),
            )
            return None

        summoner_id = getattr(summoner, "id", str(id(summoner)))
        active_list = cls._active_summons.setdefault(summoner_id, [])
        cls._summoner_refs[summoner_id] = summoner

        slot_capacity = getattr(summoner, "summon_slot_capacity", 0)
        if max_summons is not None:
            log.debug(
                "max_summons argument is deprecated; %s currently has slot capacity %s",
                summoner_id,
                slot_capacity,
            )

        if slot_capacity <= 0:
            log.debug("No summon slots available for %s", summoner_id)
            if not force_create:
                return None
            slot_capacity = 1

        if len(active_list) >= slot_capacity:
            log.debug("Summon limit (%s) reached for %s", slot_capacity, summoner_id)
            if not force_create:
                decision = cls.should_resummon(summoner_id, min_health_threshold)
                if not decision["should_resummon"]:
                    log.info("Skipping summon creation for %s: %s", summoner_id, decision["reason"])
                    return None
                if active_list:
                    worst = min(
                        active_list,
                        key=lambda s: s.hp / s.max_hp if s.max_hp > 0 else 0,
                    )
                    await cls.remove_summon(worst, "replaced_by_healthier_summon")
            else:
                if active_list:
                    await cls.remove_summon(active_list[0], "forced_replacement")
                else:
                    return None

        active_list = cls._active_summons.setdefault(summoner_id, [])

        summon = await Summon.create_from_summoner(
            summoner,
            summon_type,
            source,
            stat_multiplier,
            turns_remaining,
            override_damage_type,
        )
        counter = cls._instance_counters.get(summoner_id, 0) + 1
        cls._instance_counters[summoner_id] = counter
        summon.instance_id = f"{summoner_id}#{counter}"
        cls._active_summons[summoner_id].append(summon)
        await BUS.emit_batched_async("summon_created", summoner, summon, source)
        log.info("Created %s summon for %s from %s", summon_type, summoner_id, source)
        return summon

    @classmethod
    def get_summons(cls, summoner_id: str) -> List[Summon]:
        return cls._active_summons.get(summoner_id, []).copy()

    @classmethod
    def evaluate_summon_viability(
        cls,
        summon: Summon,
        min_health_percent: float = 0.25,
    ) -> dict:
        if not summon or summon.hp <= 0:
            return {
                "viable": False,
                "health_good": False,
                "time_remaining": 0,
                "expiring_soon": True,
                "recommendation": "Summon is dead or missing",
            }
        health_percent = summon.hp / summon.max_hp if summon.max_hp > 0 else 0
        health_good = health_percent >= min_health_percent
        time_remaining = summon.turns_remaining
        expiring_soon = time_remaining > 0 and time_remaining <= 2
        viable = health_good and not expiring_soon
        if not health_good:
            recommendation = f"Low health ({health_percent:.1%}), consider replacing"
        elif expiring_soon:
            recommendation = f"Expiring in {time_remaining} turn(s), prepare replacement"
        elif viable:
            recommendation = f"Healthy ({health_percent:.1%}), keep current summon"
        else:
            recommendation = "Unknown state"
        return {
            "viable": viable,
            "health_good": health_good,
            "time_remaining": time_remaining,
            "expiring_soon": expiring_soon,
            "recommendation": recommendation,
        }

    @classmethod
    def should_resummon(
        cls,
        summoner_id: str,
        min_health_threshold: float = 0.25,
    ) -> dict:
        existing = cls.get_summons(summoner_id)
        if not existing:
            return {
                "should_resummon": True,
                "reason": "No existing summons",
                "existing_summons": [],
                "viable_count": 0,
            }
        evaluations = []
        viable_count = 0
        for summon in existing:
            eval_result = cls.evaluate_summon_viability(summon, min_health_threshold)
            evaluations.append(
                {
                    "summon_id": summon.id,
                    "summon_type": summon.summon_type,
                    "evaluation": eval_result,
                }
            )
            if eval_result["viable"]:
                viable_count += 1
        if viable_count > 0:
            reason = f"Have {viable_count} viable summon(s), avoid unnecessary resummoning"
            should_resummon = False
        else:
            low_health = any(not e["evaluation"]["health_good"] for e in evaluations)
            expiring = any(e["evaluation"]["expiring_soon"] for e in evaluations)
            if low_health and expiring:
                reason = "Existing summons are low health and expiring soon"
            elif low_health:
                reason = "Existing summons have low health"
            elif expiring:
                reason = "Existing summons are expiring soon"
            else:
                reason = "Existing summons are not viable"
            should_resummon = True
        return {
            "should_resummon": should_resummon,
            "reason": reason,
            "existing_summons": evaluations,
            "viable_count": viable_count,
        }

    @classmethod
    async def remove_summon(cls, summon: Summon, reason: str = "unknown") -> bool:
        sid = summon.summoner_id
        if sid in cls._active_summons and summon in cls._active_summons[sid]:
            from autofighter.rooms.battle.pacing import clear_extra_turns_for

            clear_extra_turns_for(summon)
            cls._active_summons[sid].remove(summon)
            await BUS.emit_batched_async("summon_removed", summon, reason)
            if not cls._active_summons[sid]:
                del cls._active_summons[sid]
                cls._summoner_refs.pop(sid, None)
            log.debug("Removed summon %s due to %s", summon.id, reason)
            return True
        return False

    @classmethod
    async def remove_all_summons(cls, summoner_id: str, reason: str = "cleanup") -> int:
        count = 0
        if summoner_id in cls._active_summons:
            for summon in cls._active_summons[summoner_id].copy():
                removed = await cls.remove_summon(summon, reason)
                if removed:
                    count += 1
        return count

    @classmethod
    def get_all_summons(cls) -> List[Summon]:
        all_summons: List[Summon] = []
        for summons in cls._active_summons.values():
            all_summons.extend(summons)
        return all_summons

    @classmethod
    def _on_battle_start(cls, *_, **__):
        log.debug("Battle started - summon tracking active")

    @classmethod
    async def _on_battle_end(cls, *_, **__):
        total_removed = 0
        for sid in list(cls._active_summons.keys()):
            for summon in cls._active_summons[sid].copy():
                if summon.is_temporary:
                    removed = await cls.remove_summon(summon, "battle_end")
                    if removed:
                        total_removed += 1
        cls._cleanup_empty_entries()
        if total_removed > 0:
            log.debug("Cleaned up %s temporary summons at battle end", total_removed)

    @classmethod
    async def _on_turn_start(cls, entity, **__):
        eid = getattr(entity, "id", str(id(entity)))
        if eid in cls._active_summons:
            for summon in cls._active_summons[eid].copy():
                if not summon.tick_turn():
                    await cls.remove_summon(summon, "expired")

    @classmethod
    async def _on_entity_defeat(cls, entity, **__):
        eid = getattr(entity, "id", str(id(entity)))
        removed = await cls.remove_all_summons(eid, "summoner_defeated")
        if removed:
            log.debug("Removed %s summons due to summoner defeat", removed)

    @classmethod
    async def _on_entity_killed(cls, victim, *_, **__):
        if isinstance(victim, Summon):
            summoner = cls._summoner_refs.get(victim.summoner_id)
            await cls.remove_summon(victim, "defeated")
            if summoner is not None:
                await BUS.emit_async("summon_defeated", summoner, victim)
                if getattr(victim, "summon_source", "") == "becca_menagerie_bond":
                    passive = getattr(summoner, "_becca_menagerie_passive", None)
                    try:
                        if passive is None:
                            from plugins.passives.normal.becca_menagerie_bond import (
                                BeccaMenagerieBond,
                            )

                            passive = BeccaMenagerieBond()
                            setattr(summoner, "_becca_menagerie_passive", passive)

                        await passive.on_summon_defeat(summoner)
                    except Exception as e:  # pragma: no cover - defensive
                        log.warning("Error triggering summon_defeat passives: %s", e)

    @classmethod
    def add_summons_to_party(cls, party: "Party") -> int:
        added = 0
        for summon in cls.get_all_summons():
            in_party = any(
                getattr(m, "id", str(id(m))) == summon.summoner_id for m in party.members
            )
            if in_party and summon not in party.members:
                party.members.append(summon)
                added += 1
        if added:
            log.debug("Added %s summons to party for battle", added)
        return added

    @classmethod
    def cleanup(cls) -> None:
        cls._active_summons.clear()
        cls._summoner_refs.clear()
        cls._instance_counters.clear()
        log.debug("SummonManager cleaned up")

    @classmethod
    def reset_all(cls) -> None:
        cls.cleanup()
        log.debug("SummonManager reset - all tracking cleared")

    @classmethod
    def _cleanup_empty_entries(cls) -> None:
        empty = [sid for sid, summons in cls._active_summons.items() if not summons]
        for sid in empty:
            del cls._active_summons[sid]
            cls._summoner_refs.pop(sid, None)
        if empty:
            log.debug("Cleaned up %s empty summon entries", len(empty))


# Initialize the manager when module is imported
SummonManager.initialize()
