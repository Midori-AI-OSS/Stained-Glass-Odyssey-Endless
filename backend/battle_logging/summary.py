"""Data structures for battle logging."""

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List
from typing import Optional


@dataclass
class BattleEvent:
    """Represents a single battle event."""

    timestamp: datetime
    event_type: str
    attacker_id: Optional[str]
    target_id: Optional[str]
    amount: Optional[int]
    details: Dict[str, Any] = field(default_factory=dict)
    source_type: Optional[str] = None
    source_name: Optional[str] = None
    damage_type: Optional[str] = None
    effect_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BattleSummary:
    """Summary statistics for a battle."""

    battle_id: str
    start_time: datetime
    end_time: Optional[datetime]
    result: str
    party_members: List[str]
    foes: List[str]
    total_damage_dealt: Dict[str, int] = field(default_factory=dict)
    total_damage_taken: Dict[str, int] = field(default_factory=dict)
    total_healing_done: Dict[str, int] = field(default_factory=dict)
    total_hits_landed: Dict[str, int] = field(default_factory=dict)
    events: List[BattleEvent] = field(default_factory=list)

    damage_by_type: Dict[str, Dict[str, int]] = field(default_factory=dict)
    damage_by_source: Dict[str, Dict[str, int]] = field(default_factory=dict)
    damage_by_action: Dict[str, Dict[str, int]] = field(default_factory=dict)
    healing_by_source: Dict[str, Dict[str, int]] = field(default_factory=dict)
    dot_damage: Dict[str, int] = field(default_factory=dict)
    hot_healing: Dict[str, int] = field(default_factory=dict)
    relic_effects: Dict[str, int] = field(default_factory=dict)
    card_effects: Dict[str, int] = field(default_factory=dict)
    effect_applications: Dict[str, int] = field(default_factory=dict)
    party_relics: Dict[str, int] = field(default_factory=dict)

    shield_absorbed: Dict[str, int] = field(default_factory=dict)
    temporary_hp_granted: Dict[str, int] = field(default_factory=dict)
    healing_prevented: Dict[str, int] = field(default_factory=dict)

    critical_hits: Dict[str, int] = field(default_factory=dict)
    critical_damage: Dict[str, int] = field(default_factory=dict)

    resources_spent: Dict[str, Dict[str, int]] = field(default_factory=dict)
    resources_gained: Dict[str, Dict[str, int]] = field(default_factory=dict)

    kills: Dict[str, int] = field(default_factory=dict)
    dot_kills: Dict[str, int] = field(default_factory=dict)
    ultimates_used: Dict[str, int] = field(default_factory=dict)
    ultimate_failures: Dict[str, int] = field(default_factory=dict)
    self_damage: Dict[str, int] = field(default_factory=dict)
    friendly_fire: Dict[str, int] = field(default_factory=dict)


__all__ = ["BattleEvent", "BattleSummary"]

