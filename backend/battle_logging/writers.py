"""Battle logging writers and helpers."""
import asyncio
from datetime import datetime
import json
import logging
from logging.handlers import QueueHandler
from pathlib import Path
import queue
import threading
from typing import Optional

from autofighter.stats import BUS

from .handlers import AsyncQueueListener
from .handlers import TimedMemoryHandler
from .summary import BattleEvent
from .summary import BattleSummary


class BattleLogger:
    """Manages logging for individual battles."""

    def __init__(self, run_id: str, battle_index: int, base_logs_path: Optional[Path] = None):
        self.run_id = run_id
        self.battle_index = battle_index
        self.summary = BattleSummary(
            battle_id=f"{run_id}_battle_{battle_index}",
            start_time=datetime.now(),
            end_time=None,
            result="ongoing",
            party_members=[],
            foes=[]
        )

        # Create folder structure
        if base_logs_path is None:
            base_logs_path = Path(__file__).resolve().parent / "logs"
        self.base_path = base_logs_path / "runs" / run_id / "battles" / str(battle_index)
        self.raw_path = self.base_path / "raw"
        self.summary_path = self.base_path / "summary"

        self.raw_path.mkdir(parents=True, exist_ok=True)
        self.summary_path.mkdir(parents=True, exist_ok=True)

        # Set up raw logging with queue and memory buffering
        self.raw_logger = logging.getLogger(f"battle_{run_id}_{battle_index}")
        self.raw_logger.setLevel(logging.DEBUG)

        self.raw_logger.handlers.clear()

        self._log_queue = queue.SimpleQueue()
        self._file_handler = logging.FileHandler(self.raw_path / "battle.log")
        self._file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
        )
        self._memory_handler = TimedMemoryHandler(
            target=self._file_handler,
            flush_interval=15,
        )
        self._listener = AsyncQueueListener(self._log_queue, self._memory_handler)
        self._listener.start()

        queue_handler = QueueHandler(self._log_queue)
        self.raw_logger.addHandler(queue_handler)

        self.raw_logger.propagate = False

        # Event tracking
        self._lock = threading.Lock()
        self._active = True

        # Subscribe to battle events
        self._subscribe_to_events()

    def _subscribe_to_events(self):
        """Subscribe to relevant battle events."""
        BUS.subscribe("battle_start", self._on_battle_start)
        BUS.subscribe("damage_dealt", self._on_damage_dealt)
        BUS.subscribe("damage_taken", self._on_damage_taken)
        BUS.subscribe("heal", self._on_heal)
        BUS.subscribe("hit_landed", self._on_hit_landed)
        BUS.subscribe("battle_end", self._on_battle_end)

        # Enhanced event subscriptions
        BUS.subscribe("dot_tick", self._on_dot_tick)
        BUS.subscribe("hot_tick", self._on_hot_tick)
        BUS.subscribe("relic_effect", self._on_relic_effect)
        BUS.subscribe("card_effect", self._on_card_effect)
        BUS.subscribe("effect_applied", self._on_effect_applied)
        BUS.subscribe("effect_expired", self._on_effect_expired)

        # Extended tracking subscriptions
        BUS.subscribe("shield_absorbed", self._on_shield_absorbed)
        BUS.subscribe("temporary_hp_granted", self._on_temporary_hp_granted)
        BUS.subscribe("healing_prevented", self._on_healing_prevented)
        BUS.subscribe("critical_hit", self._on_critical_hit)
        BUS.subscribe("resource_spent", self._on_resource_spent)
        BUS.subscribe("resource_gained", self._on_resource_gained)

        # New events for enhanced logging
        BUS.subscribe("entity_killed", self._on_entity_killed)
        BUS.subscribe("dot_kill", self._on_dot_kill)
        BUS.subscribe("ultimate_used", self._on_ultimate_used)
        BUS.subscribe("ultimate_completed", self._on_ultimate_completed)
        BUS.subscribe("ultimate_failed", self._on_ultimate_failed)

    def _unsubscribe_from_events(self):
        """Unsubscribe from battle events."""
        BUS.unsubscribe("battle_start", self._on_battle_start)
        BUS.unsubscribe("damage_dealt", self._on_damage_dealt)
        BUS.unsubscribe("damage_taken", self._on_damage_taken)
        BUS.unsubscribe("heal", self._on_heal)
        BUS.unsubscribe("hit_landed", self._on_hit_landed)
        BUS.unsubscribe("battle_end", self._on_battle_end)

        # Enhanced event unsubscriptions
        BUS.unsubscribe("dot_tick", self._on_dot_tick)
        BUS.unsubscribe("hot_tick", self._on_hot_tick)
        BUS.unsubscribe("relic_effect", self._on_relic_effect)
        BUS.unsubscribe("card_effect", self._on_card_effect)
        BUS.unsubscribe("effect_applied", self._on_effect_applied)
        BUS.unsubscribe("effect_expired", self._on_effect_expired)

        # Extended tracking unsubscriptions
        BUS.unsubscribe("shield_absorbed", self._on_shield_absorbed)
        BUS.unsubscribe("temporary_hp_granted", self._on_temporary_hp_granted)
        BUS.unsubscribe("healing_prevented", self._on_healing_prevented)
        BUS.unsubscribe("critical_hit", self._on_critical_hit)
        BUS.unsubscribe("resource_spent", self._on_resource_spent)
        BUS.unsubscribe("resource_gained", self._on_resource_gained)

        # New events unsubscriptions
        BUS.unsubscribe("entity_killed", self._on_entity_killed)
        BUS.unsubscribe("dot_kill", self._on_dot_kill)
        BUS.unsubscribe("ultimate_used", self._on_ultimate_used)
        BUS.unsubscribe("ultimate_completed", self._on_ultimate_completed)
        BUS.unsubscribe("ultimate_failed", self._on_ultimate_failed)

    def _log_event(self, event: BattleEvent):
        """Log an event to both raw logs and summary."""
        if not self._active:
            return

        with self._lock:
            # Add to summary
            self.summary.events.append(event)

            # Track per-entity damage by element
            if (
                event.damage_type
                and event.amount is not None
                and event.attacker_id is not None
            ):
                types = self.summary.damage_by_type.setdefault(event.attacker_id, {})
                types[event.damage_type] = types.get(event.damage_type, 0) + event.amount

            # Log to raw file with enhanced details
            details_str = ""
            if event.source_type:
                details_str += f" [source_type: {event.source_type}]"
            if event.source_name:
                details_str += f" [source_name: {event.source_name}]"
            if event.damage_type:
                details_str += f" [damage_type: {event.damage_type}]"
            if event.effect_details:
                details_str += f" [effect: {event.effect_details}]"
            if event.details:
                details_str += f" [details: {event.details}]"

            self.raw_logger.info(
                f"{event.event_type}: {event.attacker_id or 'N/A'} -> {event.target_id or 'N/A'} "
                f"(amount: {event.amount or 'N/A'}){details_str}"
            )

    def _on_battle_start(self, entity):
        """Handle battle start event."""
        entity_id = getattr(entity, 'id', str(entity))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="battle_start",
            attacker_id=None,
            target_id=entity_id,
            amount=None,
            details={"entity_type": type(entity).__name__}
        )
        self._log_event(event)

        # Participant lists are set by the battle controller; avoid guessing here
        # to prevent misclassification.

    def _on_damage_dealt(self, attacker, target, amount, source_type="attack", source_name=None, damage_type=None, action_name=None):
        """Handle damage dealt event."""
        attacker_id = getattr(attacker, 'id', str(attacker))
        target_id = getattr(target, 'id', str(target))

        if source_type == "attack" and not action_name:
            action_name = "Normal Attack"

        # Get damage type if not provided
        if damage_type is None and hasattr(attacker, 'damage_type'):
            damage_type = getattr(attacker.damage_type, 'id', str(attacker.damage_type))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="damage_dealt",
            attacker_id=attacker_id,
            target_id=target_id,
            amount=amount,
            source_type=source_type,
            source_name=source_name,
            damage_type=damage_type
        )
        self._log_event(event)
        # Determine relationships for self damage and friendly fire
        if attacker_id == target_id:
            self.summary.self_damage[attacker_id] = (
                self.summary.self_damage.get(attacker_id, 0) + amount
            )
        else:
            attacker_is_party = attacker_id in self.summary.party_members
            attacker_is_foe = attacker_id in self.summary.foes
            target_is_party = target_id in self.summary.party_members
            target_is_foe = target_id in self.summary.foes

            if (attacker_is_party and target_is_party) or (attacker_is_foe and target_is_foe):
                self.summary.friendly_fire[attacker_id] = (
                    self.summary.friendly_fire.get(attacker_id, 0) + amount
                )

        # Update summary stats
        self.summary.total_damage_dealt[attacker_id] = (
            self.summary.total_damage_dealt.get(attacker_id, 0) + amount
        )

        # Track damage by source type
        if source_type not in self.summary.damage_by_source:
            self.summary.damage_by_source[source_type] = {}
        self.summary.damage_by_source[source_type][attacker_id] = self.summary.damage_by_source[source_type].get(attacker_id, 0) + amount

        # Track damage by action name for more specific breakdown
        if action_name:
            if attacker_id not in self.summary.damage_by_action:
                self.summary.damage_by_action[attacker_id] = {}
            self.summary.damage_by_action[attacker_id][action_name] = self.summary.damage_by_action[attacker_id].get(action_name, 0) + amount

    def _on_damage_taken(self, target, attacker, amount):
        """Handle damage taken event."""
        attacker_id = getattr(attacker, 'id', str(attacker)) if attacker else None
        target_id = getattr(target, 'id', str(target))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="damage_taken",
            attacker_id=attacker_id,
            target_id=target_id,
            amount=amount
        )
        self._log_event(event)

        # Update summary stats
        self.summary.total_damage_taken[target_id] = self.summary.total_damage_taken.get(target_id, 0) + amount

    def _on_heal(self, healer, target, amount, source_type="heal", source_name=None):
        """Handle healing event."""
        healer_id = getattr(healer, 'id', str(healer)) if healer else None
        target_id = getattr(target, 'id', str(target))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="heal",
            attacker_id=healer_id,
            target_id=target_id,
            amount=amount,
            source_type=source_type,
            source_name=source_name
        )
        self._log_event(event)

        # Update summary stats
        if healer_id:
            self.summary.total_healing_done[healer_id] = self.summary.total_healing_done.get(healer_id, 0) + amount

            # Track healing by source type
            if source_type not in self.summary.healing_by_source:
                self.summary.healing_by_source[source_type] = {}
            self.summary.healing_by_source[source_type][healer_id] = self.summary.healing_by_source[source_type].get(healer_id, 0) + amount

            # ALSO track healing in damage_by_action so it shows up in "Damage by Action" UI
            # Determine the action name based on source type
            action_name = "Healing"
            if source_type == "hot":
                action_name = "HoT Healing"
            elif source_type == "ultimate":
                action_name = f"{source_name or 'Ultimate'} Healing"
            elif source_name:
                action_name = f"{source_name} Healing"

            if healer_id not in self.summary.damage_by_action:
                self.summary.damage_by_action[healer_id] = {}
            self.summary.damage_by_action[healer_id][action_name] = self.summary.damage_by_action[healer_id].get(action_name, 0) + amount

    def _on_hit_landed(self, attacker, target, amount, source_type="attack", source_name=None, action_name=None):
        """Handle hit landed event."""
        attacker_id = getattr(attacker, 'id', str(attacker))
        target_id = getattr(target, 'id', str(target))

        # Get damage type if available
        damage_type = None
        if hasattr(attacker, 'damage_type'):
            damage_type = getattr(attacker.damage_type, 'id', str(attacker.damage_type))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="hit_landed",
            attacker_id=attacker_id,
            target_id=target_id,
            amount=amount,
            source_type=source_type,
            source_name=source_name,
            damage_type=damage_type
        )
        self._log_event(event)

        # Update summary stats
        self.summary.total_hits_landed[attacker_id] = self.summary.total_hits_landed.get(attacker_id, 0) + 1

    def _on_battle_end(self, entity):
        """Handle battle end event."""
        entity_id = getattr(entity, 'id', str(entity))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="battle_end",
            attacker_id=None,
            target_id=entity_id,
            amount=None,
            details={"entity_type": type(entity).__name__}
        )
        self._log_event(event)

    def _on_dot_tick(self, attacker, target, amount, dot_name=None, effect_details=None):
        """Handle DoT tick event."""
        attacker_id = getattr(attacker, 'id', str(attacker))
        target_id = getattr(target, 'id', str(target))

        # Get damage type if available
        damage_type = None
        if hasattr(attacker, 'damage_type'):
            damage_type = getattr(attacker.damage_type, 'id', str(attacker.damage_type))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="dot_tick",
            attacker_id=attacker_id,
            target_id=target_id,
            amount=amount,
            source_type="dot",
            source_name=dot_name,
            damage_type=damage_type,
            effect_details=effect_details or {}
        )
        self._log_event(event)

        # Update DoT damage tracking
        self.summary.dot_damage[attacker_id] = self.summary.dot_damage.get(attacker_id, 0) + amount

        # Track damage by source type
        if "dot" not in self.summary.damage_by_source:
            self.summary.damage_by_source["dot"] = {}
        self.summary.damage_by_source["dot"][attacker_id] = self.summary.damage_by_source["dot"].get(attacker_id, 0) + amount

        # Fold DoT into headline totals
        self.summary.total_damage_dealt[attacker_id] = self.summary.total_damage_dealt.get(attacker_id, 0) + amount
        self.summary.total_damage_taken[target_id] = self.summary.total_damage_taken.get(target_id, 0) + amount

    def _on_hot_tick(self, healer, target, amount, hot_name=None, effect_details=None):
        """Handle HoT tick event."""
        healer_id = getattr(healer, 'id', str(healer)) if healer else None
        target_id = getattr(target, 'id', str(target))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="hot_tick",
            attacker_id=healer_id,
            target_id=target_id,
            amount=amount,
            source_type="hot",
            source_name=hot_name,
            effect_details=effect_details or {}
        )
        self._log_event(event)

        # Update HoT healing tracking
        if healer_id:
            self.summary.hot_healing[healer_id] = self.summary.hot_healing.get(healer_id, 0) + amount

            # Track healing by source type
            if "hot" not in self.summary.healing_by_source:
                self.summary.healing_by_source["hot"] = {}
            self.summary.healing_by_source["hot"][healer_id] = self.summary.healing_by_source["hot"].get(healer_id, 0) + amount

            # Fold HoT into headline totals
            self.summary.total_healing_done[healer_id] = self.summary.total_healing_done.get(healer_id, 0) + amount

    def _on_relic_effect(self, relic_name, entity, effect_type=None, amount=None, details=None):
        """Handle relic effect event."""
        entity_id = getattr(entity, 'id', str(entity))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="relic_effect",
            attacker_id=entity_id,
            target_id=entity_id,
            amount=amount,
            source_type="relic_effect",
            source_name=relic_name,
            effect_details=details or {"effect_type": effect_type}
        )
        self._log_event(event)

        # Update relic effect tracking
        self.summary.relic_effects[relic_name] = self.summary.relic_effects.get(relic_name, 0) + 1

        # Track aftertaste and similar effects as specific actions for damage breakdown
        if relic_name == "aftertaste" and effect_type == "damage" and amount:
            if entity_id not in self.summary.damage_by_action:
                self.summary.damage_by_action[entity_id] = {}

            # Create element-specific action name for Aftertaste to show mixed colors
            action_name = "Aftertaste"
            if details and "random_damage_type" in details:
                damage_type = details["random_damage_type"]
                action_name = f"Aftertaste ({damage_type})"

            self.summary.damage_by_action[entity_id][action_name] = self.summary.damage_by_action[entity_id].get(action_name, 0) + amount

    def _on_card_effect(self, card_name, entity, effect_type=None, amount=None, details=None):
        """Handle card effect event."""
        entity_id = getattr(entity, 'id', str(entity))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="card_effect",
            attacker_id=entity_id,
            target_id=entity_id,
            amount=amount,
            source_type="card_effect",
            source_name=card_name,
            effect_details=details or {"effect_type": effect_type}
        )
        self._log_event(event)

        # Update card effect tracking
        self.summary.card_effects[card_name] = self.summary.card_effects.get(card_name, 0) + 1

    def _on_effect_applied(self, effect_name, entity, details=None):
        """Handle effect application event."""
        entity_id = getattr(entity, 'id', str(entity))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="effect_applied",
            attacker_id=None,
            target_id=entity_id,
            amount=None,
            source_type="effect",
            source_name=effect_name,
            effect_details=details or {}
        )
        self._log_event(event)

        # Update effect application tracking
        self.summary.effect_applications[effect_name] = self.summary.effect_applications.get(effect_name, 0) + 1

    def _on_effect_expired(self, effect_name, entity, details=None):
        """Handle effect expiration event."""
        entity_id = getattr(entity, 'id', str(entity))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="effect_expired",
            attacker_id=None,
            target_id=entity_id,
            amount=None,
            source_type="effect",
            source_name=effect_name,
            effect_details=details or {}
        )
        self._log_event(event)

    def _on_shield_absorbed(self, entity, amount, source_type="shield", source_name=None):
        """Handle shield absorption event."""
        entity_id = getattr(entity, 'id', str(entity))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="shield_absorbed",
            attacker_id=None,
            target_id=entity_id,
            amount=amount,
            source_type=source_type,
            source_name=source_name
        )
        self._log_event(event)

        # Update shield absorption tracking
        self.summary.shield_absorbed[entity_id] = self.summary.shield_absorbed.get(entity_id, 0) + amount

    def _on_temporary_hp_granted(self, entity, amount, source_type="temp_hp", source_name=None):
        """Handle temporary HP granted event."""
        entity_id = getattr(entity, 'id', str(entity))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="temporary_hp_granted",
            attacker_id=None,
            target_id=entity_id,
            amount=amount,
            source_type=source_type,
            source_name=source_name
        )
        self._log_event(event)

        # Update temporary HP tracking
        self.summary.temporary_hp_granted[entity_id] = self.summary.temporary_hp_granted.get(entity_id, 0) + amount

    def _on_healing_prevented(self, entity, amount, source_type="heal_prevention", source_name=None):
        """Handle healing prevented event."""
        entity_id = getattr(entity, 'id', str(entity))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="healing_prevented",
            attacker_id=None,
            target_id=entity_id,
            amount=amount,
            source_type=source_type,
            source_name=source_name
        )
        self._log_event(event)

        # Update healing prevention tracking
        self.summary.healing_prevented[entity_id] = self.summary.healing_prevented.get(entity_id, 0) + amount

    def _on_critical_hit(self, attacker, target, damage, source_type="attack", source_name=None):
        """Handle critical hit event."""
        attacker_id = getattr(attacker, 'id', str(attacker))
        target_id = getattr(target, 'id', str(target))

        # Get damage type if available
        damage_type = None
        if hasattr(attacker, 'damage_type'):
            damage_type = getattr(attacker.damage_type, 'id', str(attacker.damage_type))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="critical_hit",
            attacker_id=attacker_id,
            target_id=target_id,
            amount=damage,
            source_type=source_type,
            source_name=source_name,
            damage_type=damage_type,
            effect_details={"is_critical": True}
        )
        self._log_event(event)

        # Update critical hit tracking
        self.summary.critical_hits[attacker_id] = self.summary.critical_hits.get(attacker_id, 0) + 1
        self.summary.critical_damage[attacker_id] = self.summary.critical_damage.get(attacker_id, 0) + damage

    def _on_resource_spent(self, entity, resource_type, amount, source_type="resource", source_name=None):
        """Handle resource spent event."""
        entity_id = getattr(entity, 'id', str(entity))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="resource_spent",
            attacker_id=entity_id,
            target_id=entity_id,
            amount=amount,
            source_type=source_type,
            source_name=source_name,
            effect_details={"resource_type": resource_type}
        )
        self._log_event(event)

        # Update resource tracking
        if entity_id not in self.summary.resources_spent:
            self.summary.resources_spent[entity_id] = {}
        self.summary.resources_spent[entity_id][resource_type] = self.summary.resources_spent[entity_id].get(resource_type, 0) + amount

    def _on_resource_gained(self, entity, resource_type, amount, source_type="resource", source_name=None):
        """Handle resource gained event."""
        entity_id = getattr(entity, 'id', str(entity))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="resource_gained",
            attacker_id=entity_id,
            target_id=entity_id,
            amount=amount,
            source_type=source_type,
            source_name=source_name,
            effect_details={"resource_type": resource_type}
        )
        self._log_event(event)

        # Update resource tracking
        if entity_id not in self.summary.resources_gained:
            self.summary.resources_gained[entity_id] = {}
        self.summary.resources_gained[entity_id][resource_type] = self.summary.resources_gained[entity_id].get(resource_type, 0) + amount

    def finalize_battle(self, result: str = "completed"):
        """Finalize the battle and write summary."""
        if not self._active:
            return

        with self._lock:
            self.summary.end_time = datetime.now()
            self.summary.result = result

            # Write summary to JSON
            summary_data = {
                "battle_id": self.summary.battle_id,
                "start_time": self.summary.start_time.isoformat(),
                "end_time": self.summary.end_time.isoformat() if self.summary.end_time else None,
                "result": self.summary.result,
                "party_members": self.summary.party_members,
                "foes": self.summary.foes,
                "total_damage_dealt": self.summary.total_damage_dealt,
                "total_damage_taken": self.summary.total_damage_taken,
                "total_healing_done": self.summary.total_healing_done,
                "total_hits_landed": self.summary.total_hits_landed,
                "self_damage": self.summary.self_damage,
                "friendly_fire": self.summary.friendly_fire,
                "event_count": len(self.summary.events),
                "duration_seconds": (
                    (self.summary.end_time - self.summary.start_time).total_seconds()
                    if self.summary.end_time else None
                ),
                "party_relics": self.summary.party_relics,
                # Enhanced tracking data
                "damage_by_type": self.summary.damage_by_type,
                "damage_by_source": self.summary.damage_by_source,
                "damage_by_action": self.summary.damage_by_action,
                "healing_by_source": self.summary.healing_by_source,
                "dot_damage": self.summary.dot_damage,
                "hot_healing": self.summary.hot_healing,
                "relic_effects": self.summary.relic_effects,
                "card_effects": self.summary.card_effects,
                "effect_applications": self.summary.effect_applications,

                # Extended tracking data
                "shield_absorbed": self.summary.shield_absorbed,
                "temporary_hp_granted": self.summary.temporary_hp_granted,
                "healing_prevented": self.summary.healing_prevented,
                "critical_hits": self.summary.critical_hits,
                "critical_damage": self.summary.critical_damage,
                "resources_spent": self.summary.resources_spent,
                "resources_gained": self.summary.resources_gained,

                # Combat tracking data (missing from original export)
                "kills": self.summary.kills,
                "dot_kills": self.summary.dot_kills,
                "ultimates_used": self.summary.ultimates_used,
                "ultimate_failures": self.summary.ultimate_failures
            }

            # Write summary JSON
            with open(self.summary_path / "battle_summary.json", "w") as f:
                json.dump(summary_data, f, indent=2)

            # Write detailed events
            events_data = [
                {
                    "timestamp": event.timestamp.isoformat(),
                    "event_type": event.event_type,
                    "attacker_id": event.attacker_id,
                    "target_id": event.target_id,
                    "amount": event.amount,
                    "details": event.details,
                    "source_type": event.source_type,
                    "source_name": event.source_name,
                    "damage_type": event.damage_type,
                    "effect_details": event.effect_details
                }
                for event in self.summary.events
            ]

            with open(self.summary_path / "events.json", "w") as f:
                json.dump(events_data, f, indent=2)

            # Write human-readable summary
            self._write_human_summary()

            # Cleanup
            self._unsubscribe_from_events()
            self._active = False

        async def _flush_async() -> None:
            await asyncio.to_thread(self._shutdown_handlers)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(_flush_async())
        else:
            loop.create_task(_flush_async())

    def _shutdown_handlers(self) -> None:
        """Flush and close logging handlers."""
        self._listener.stop()
        self._memory_handler.flush()
        self._memory_handler.close()
        self._file_handler.flush()
        self._file_handler.close()
        for handler in self.raw_logger.handlers:
            handler.close()
        self.raw_logger.handlers.clear()

    def _write_human_summary(self):
        """Write a human-readable summary."""
        duration = (
            (self.summary.end_time - self.summary.start_time).total_seconds()
            if self.summary.end_time else 0
        )

        lines = [
            f"Battle Summary: {self.summary.battle_id}",
            f"{'=' * 50}",
            f"Result: {self.summary.result.upper()}",
            f"Duration: {duration:.1f} seconds",
            f"Start: {self.summary.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"End: {self.summary.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.summary.end_time else 'N/A'}",
            "",
            "Participants:",
            f"  Party: {', '.join(self.summary.party_members) if self.summary.party_members else 'None'}",
            f"  Foes: {', '.join(self.summary.foes) if self.summary.foes else 'None'}",
            "",
            "Damage Dealt:",
        ]

        for entity, damage in sorted(self.summary.total_damage_dealt.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {entity}: {damage}")

        lines.extend([
            "",
            "Damage Taken:",
        ])

        for entity, damage in sorted(self.summary.total_damage_taken.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {entity}: {damage}")

        if self.summary.total_healing_done:
            lines.extend([
                "",
                "Healing Done:",
            ])
            for entity, healing in sorted(self.summary.total_healing_done.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {entity}: {healing}")

        lines.extend([
            "",
            "Hits Landed:",
        ])

        for entity, hits in sorted(self.summary.total_hits_landed.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"  {entity}: {hits}")

        # Enhanced tracking summaries
        if self.summary.damage_by_type:
            lines.extend([
                "",
                "Damage by Element:",
            ])
            for entity, types in self.summary.damage_by_type.items():
                lines.append(f"  {entity}:")
                for dmg_type, amount in sorted(types.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"    {dmg_type}: {amount}")

        if self.summary.damage_by_source:
            lines.extend([
                "",
                "Damage by Source Type:",
            ])
            for source_type, entities in self.summary.damage_by_source.items():
                lines.append(f"  {source_type.upper()}:")
                for entity, damage in sorted(entities.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"    {entity}: {damage}")

        if self.summary.healing_by_source:
            lines.extend([
                "",
                "Healing by Source Type:",
            ])
            for source_type, entities in self.summary.healing_by_source.items():
                lines.append(f"  {source_type.upper()}:")
                for entity, healing in sorted(entities.items(), key=lambda x: x[1], reverse=True):
                    lines.append(f"    {entity}: {healing}")

        if self.summary.dot_damage:
            lines.extend([
                "",
                "DoT Damage Dealt:",
            ])
            for entity, damage in sorted(self.summary.dot_damage.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {entity}: {damage}")

        if self.summary.hot_healing:
            lines.extend([
                "",
                "HoT Healing Done:",
            ])
            for entity, healing in sorted(self.summary.hot_healing.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {entity}: {healing}")

        if self.summary.relic_effects:
            lines.extend([
                "",
                "Relic Effects Triggered:",
            ])
            for relic, count in sorted(self.summary.relic_effects.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {relic}: {count} times")

        if self.summary.party_relics:
            lines.extend([
                "",
                "Relics Equipped:",
            ])
            for rid, qty in sorted(self.summary.party_relics.items()):
                lines.append(f"  {rid}: x{qty}")

        if self.summary.card_effects:
            lines.extend([
                "",
                "Card Effects Triggered:",
            ])
            for card, count in sorted(self.summary.card_effects.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {card}: {count} times")

        if self.summary.effect_applications:
            lines.extend([
                "",
                "Effects Applied:",
            ])
            for effect, count in sorted(self.summary.effect_applications.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {effect}: {count} times")

        # Extended tracking summaries
        if self.summary.shield_absorbed:
            lines.extend([
                "",
                "Shield Damage Absorbed:",
            ])
            for entity, absorbed in sorted(self.summary.shield_absorbed.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {entity}: {absorbed}")

        if self.summary.temporary_hp_granted:
            lines.extend([
                "",
                "Temporary HP Granted:",
            ])
            for entity, temp_hp in sorted(self.summary.temporary_hp_granted.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {entity}: {temp_hp}")

        if self.summary.healing_prevented:
            lines.extend([
                "",
                "Healing Prevented:",
            ])
            for entity, prevented in sorted(self.summary.healing_prevented.items(), key=lambda x: x[1], reverse=True):
                lines.append(f"  {entity}: {prevented}")

        if self.summary.critical_hits:
            lines.extend([
                "",
                "Critical Hits:",
            ])
            for entity, crits in sorted(self.summary.critical_hits.items(), key=lambda x: x[1], reverse=True):
                crit_dmg = self.summary.critical_damage.get(entity, 0)
                lines.append(f"  {entity}: {crits} crits ({crit_dmg} damage)")

        if self.summary.resources_spent:
            lines.extend([
                "",
                "Resources Spent:",
            ])
            for entity, resources in self.summary.resources_spent.items():
                lines.append(f"  {entity}:")
                for resource_type, amount in sorted(resources.items()):
                    lines.append(f"    {resource_type}: {amount}")

        if self.summary.resources_gained:
            lines.extend([
                "",
                "Resources Gained:",
            ])
            for entity, resources in self.summary.resources_gained.items():
                lines.append(f"  {entity}:")
                for resource_type, amount in sorted(resources.items()):
                    lines.append(f"    {resource_type}: {amount}")

        lines.extend([
            "",
            f"Total Events: {len(self.summary.events)}",
        ])

        with open(self.summary_path / "human_summary.txt", "w") as f:
            f.write("\n".join(lines))

    def _on_entity_killed(self, victim, killer, amount, source_type="death", details=None):
        """Handle entity killed event."""
        victim_id = getattr(victim, 'id', str(victim))
        killer_id = getattr(killer, 'id', str(killer)) if killer else None

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="entity_killed",
            attacker_id=killer_id,
            target_id=victim_id,
            amount=0,
            source_type=source_type,
            source_name="death",
            effect_details=details or {}
        )
        self._log_event(event)

        # Update kill tracking
        if killer_id:
            self.summary.kills[killer_id] = self.summary.kills.get(killer_id, 0) + 1

    def _on_dot_kill(self, attacker, target, damage, dot_name, details=None):
        """Handle DOT kill event."""
        attacker_id = getattr(attacker, 'id', str(attacker))
        target_id = getattr(target, 'id', str(target))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="dot_kill",
            attacker_id=attacker_id,
            target_id=target_id,
            amount=damage,
            source_type="dot",
            source_name=dot_name,
            effect_details=details or {}
        )
        self._log_event(event)

        # Update DOT kill tracking
        self.summary.dot_kills[attacker_id] = self.summary.dot_kills.get(attacker_id, 0) + 1

    def _on_ultimate_used(self, caster, target, amount, source_type="ultimate", details=None):
        """Handle ultimate used event."""
        caster_id = getattr(caster, 'id', str(caster))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="ultimate_used",
            attacker_id=caster_id,
            target_id=None,
            amount=0,
            source_type=source_type,
            source_name="ultimate",
            effect_details=details or {}
        )
        self._log_event(event)

        # Update ultimate usage tracking
        self.summary.ultimates_used[caster_id] = self.summary.ultimates_used.get(caster_id, 0) + 1

    def _on_ultimate_completed(self, caster, target, amount, source_type="ultimate", details=None):
        """Handle ultimate completed event."""
        caster_id = getattr(caster, 'id', str(caster))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="ultimate_completed",
            attacker_id=caster_id,
            target_id=None,
            amount=0,
            source_type=source_type,
            source_name="ultimate",
            effect_details=details or {}
        )
        self._log_event(event)

    def _on_ultimate_failed(self, caster, target, amount, source_type="ultimate", details=None):
        """Handle ultimate failed event."""
        caster_id = getattr(caster, 'id', str(caster))

        event = BattleEvent(
            timestamp=datetime.now(),
            event_type="ultimate_failed",
            attacker_id=caster_id,
            target_id=None,
            amount=0,
            source_type=source_type,
            source_name="ultimate",
            effect_details=details or {}
        )
        self._log_event(event)

        # Update ultimate failure tracking
        self.summary.ultimate_failures[caster_id] = self.summary.ultimate_failures.get(caster_id, 0) + 1


class RunLogger:
    """Manages logging for an entire run."""

    def __init__(self, run_id: str, base_logs_path: Optional[Path] = None):
        self.run_id = run_id
        self.battle_count = 0
        self.current_battle_logger: Optional[BattleLogger] = None
        self.base_logs_path = base_logs_path

        # Create run folder
        if base_logs_path is None:
            base_logs_path = Path(__file__).resolve().parent / "logs"
        self.run_path = base_logs_path / "runs" / run_id
        self.run_path.mkdir(parents=True, exist_ok=True)
        # Determine next battle index by scanning existing battle folders (survive restarts)
        battles_root = self.run_path / "battles"
        battles_root.mkdir(parents=True, exist_ok=True)
        try:
            existing = [int(p.name) for p in battles_root.iterdir() if p.is_dir() and p.name.isdigit()]
            self.battle_count = max(existing) if existing else 0
        except Exception:
            self.battle_count = 0

    def start_battle(self) -> BattleLogger:
        """Start logging a new battle."""
        if self.current_battle_logger:
            self.current_battle_logger.finalize_battle("interrupted")

        self.battle_count += 1
        self.current_battle_logger = BattleLogger(self.run_id, self.battle_count, self.base_logs_path)
        return self.current_battle_logger

    def end_battle(self, result: str = "completed"):
        """End the current battle."""
        if self.current_battle_logger:
            self.current_battle_logger.finalize_battle(result)
            self.current_battle_logger = None

    def finalize_run(self):
        """Finalize the entire run."""
        if self.current_battle_logger:
            self.current_battle_logger.finalize_battle("run_ended")
            self.current_battle_logger = None


# Global run logger instance
_current_run_logger: Optional[RunLogger] = None
_run_logger_lock = threading.Lock()


def start_run_logging(run_id: str) -> RunLogger:
    """Start logging for a new run."""
    global _current_run_logger
    with _run_logger_lock:
        if _current_run_logger:
            _current_run_logger.finalize_run()
        _current_run_logger = RunLogger(run_id)
        return _current_run_logger


def get_current_run_logger() -> Optional[RunLogger]:
    """Get the current run logger."""
    return _current_run_logger


def end_run_logging():
    """End logging for the current run."""
    global _current_run_logger
    with _run_logger_lock:
        if _current_run_logger:
            _current_run_logger.finalize_run()
            _current_run_logger = None


def start_battle_logging() -> Optional[BattleLogger]:
    """Start logging for a new battle."""
    if _current_run_logger:
        return _current_run_logger.start_battle()
    return None


def end_battle_logging(result: str = "completed"):
    """End logging for the current battle."""
    if _current_run_logger:
        _current_run_logger.end_battle(result)
