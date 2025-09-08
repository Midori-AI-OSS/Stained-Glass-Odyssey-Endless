"""
Turn-based battle recording system for real-time animated combat.

This module provides functionality to record battle actions turn-by-turn,
allowing the frontend to play back battles with proper animations and timing.
"""
import asyncio
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
import logging
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from autofighter.stats import BUS

log = logging.getLogger(__name__)


@dataclass
class TurnAction:
    """Represents a single action taken during a battle turn."""
    action_id: str  # Unique identifier for this action
    timestamp: datetime
    action_type: str  # 'attack', 'heal', 'effect', 'death', 'summon', etc.
    actor_id: str  # Who performed the action
    target_id: Optional[str]  # Primary target (None for self-targeting or area effects)
    targets: List[str] = field(default_factory=list)  # All affected targets (for multi-target actions)

    # Damage/healing information
    amount: int = 0  # Primary damage/healing amount
    amounts: Dict[str, int] = field(default_factory=dict)  # Per-target amounts for multi-target
    damage_type: Optional[str] = None  # Fire, Ice, Lightning, etc.
    is_critical: bool = False

    # Animation and visual cues
    animation_name: Optional[str] = None  # .efkefc file to play
    effect_color: Optional[str] = None  # Hex color for damage numbers/effects

    # Status effects and additional data
    status_effects: List[Dict[str, Any]] = field(default_factory=list)  # Applied/removed effects
    action_name: str = "Unknown Action"  # Human-readable action name
    description: str = ""  # Detailed description for UI

    # Timing and flow control
    duration_ms: int = 1000  # Suggested animation duration in milliseconds
    requires_confirmation: bool = True  # Whether frontend should wait for user confirmation

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'action_id': self.action_id,
            'timestamp': self.timestamp.isoformat(),
            'action_type': self.action_type,
            'actor_id': self.actor_id,
            'target_id': self.target_id,
            'targets': self.targets,
            'amount': self.amount,
            'amounts': self.amounts,
            'damage_type': self.damage_type,
            'is_critical': self.is_critical,
            'animation_name': self.animation_name,
            'effect_color': self.effect_color,
            'status_effects': self.status_effects,
            'action_name': self.action_name,
            'description': self.description,
            'duration_ms': self.duration_ms,
            'requires_confirmation': self.requires_confirmation
        }


@dataclass
class BattleRecording:
    """Complete recording of a battle with turn-by-turn actions."""
    battle_id: str
    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None

    # Battle participants
    party_members: List[str] = field(default_factory=list)
    foes: List[str] = field(default_factory=list)

    # Turn-by-turn recording
    actions: List[TurnAction] = field(default_factory=list)
    current_action_index: int = 0  # Next action to be sent to frontend

    # Battle state tracking
    is_complete: bool = False
    result: Optional[str] = None  # 'victory', 'defeat', 'ongoing'
    awaiting_frontend: bool = False  # True when waiting for frontend confirmation

    # Current battle state (for frontend display)
    current_party_state: List[Dict[str, Any]] = field(default_factory=list)
    current_foe_state: List[Dict[str, Any]] = field(default_factory=list)

    def get_next_action(self) -> Optional[TurnAction]:
        """Get the next action to send to frontend."""
        if self.current_action_index < len(self.actions):
            return self.actions[self.current_action_index]
        return None

    def confirm_action_complete(self) -> bool:
        """Mark current action as complete and advance to next."""
        if self.current_action_index < len(self.actions):
            self.current_action_index += 1
            self.awaiting_frontend = False
            return True
        return False

    def add_action(self, action: TurnAction) -> None:
        """Add a new action to the recording."""
        self.actions.append(action)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'battle_id': self.battle_id,
            'run_id': self.run_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'party_members': self.party_members,
            'foes': self.foes,
            'actions': [action.to_dict() for action in self.actions],
            'current_action_index': self.current_action_index,
            'is_complete': self.is_complete,
            'result': self.result,
            'awaiting_frontend': self.awaiting_frontend,
            'current_party_state': self.current_party_state,
            'current_foe_state': self.current_foe_state
        }


# Global storage for active battle recordings
battle_recordings: Dict[str, BattleRecording] = {}


def get_animation_for_damage_type(damage_type: Optional[str], action_type: str = 'attack') -> str:
    """Map damage types to appropriate .efkefc animation files."""
    if not damage_type:
        damage_type = 'Generic'

    damage_type = damage_type.lower()

    # Map damage types to animation files based on existing effects
    animation_map = {
        'fire': {
            'attack': 'HitFire.efkefc',
            'spell': 'Fire1.efkefc',
            'breath': 'BreathFire.efkefc',
            'claw': 'ClawFire.efkefc'
        },
        'ice': {
            'attack': 'HitIce.efkefc',
            'spell': 'Ice1.efkefc',
            'breath': 'BreathIce.efkefc',
            'claw': 'ClawIce.efkefc'
        },
        'lightning': {
            'attack': 'HitThunder.efkefc',
            'spell': 'Thunder1.efkefc',
            'breath': 'BreathThunder.efkefc',
            'claw': 'ClawThunder.efkefc'
        },
        'thunder': {
            'attack': 'HitThunder.efkefc',
            'spell': 'Thunder1.efkefc',
            'breath': 'BreathThunder.efkefc',
            'claw': 'ClawThunder.efkefc'
        },
        'water': {
            'attack': 'HitPhysical.efkefc',
            'spell': 'Water1.efkefc',
            'breath': 'BreathWater.efkefc'
        },
        'earth': {
            'attack': 'HitPhysical.efkefc',
            'spell': 'Earth1.efkefc',
            'breath': 'BreathEarth.efkefc'
        },
        'wind': {
            'attack': 'HitSpecial1.efkefc',
            'spell': 'Wind1.efkefc',
            'breath': 'BreathWind.efkefc'
        },
        'light': {
            'attack': 'HitSpecial2.efkefc',
            'spell': 'Light1.efkefc',
            'breath': 'BreathLight.efkefc'
        },
        'dark': {
            'attack': 'HitSpecial1.efkefc',
            'spell': 'Darkness1.efkefc',
            'breath': 'BreathDarkness.efkefc'
        },
        'generic': {
            'attack': 'HitPhysical.efkefc',
            'spell': 'HitEffect.efkefc'
        }
    }

    # Get animation mapping for damage type
    type_animations = animation_map.get(damage_type, animation_map['generic'])

    # Return specific animation for action type, fallback to attack
    return type_animations.get(action_type, type_animations.get('attack', 'HitEffect.efkefc'))


def get_color_for_damage_type(damage_type: Optional[str]) -> str:
    """Get hex color for damage type to color damage numbers."""
    if not damage_type:
        return '#FFFFFF'  # White for generic

    damage_type = damage_type.lower()

    color_map = {
        'fire': '#FF4444',      # Red
        'ice': '#44AAFF',       # Light Blue
        'lightning': '#FFFF44', # Yellow
        'thunder': '#FFFF44',   # Yellow
        'water': '#4488FF',     # Blue
        'earth': '#88AA44',     # Earth Green
        'wind': '#AAFFAA',      # Light Green
        'light': '#FFFFAA',     # Light Yellow
        'dark': '#AA44AA',      # Purple
        'generic': '#FFFFFF'    # White
    }

    return color_map.get(damage_type, '#FFFFFF')


def create_attack_action(
    actor_id: str,
    target_id: str,
    damage: int,
    damage_type: Optional[str] = None,
    is_critical: bool = False,
    action_name: str = "Attack"
) -> TurnAction:
    """Create a standard attack action."""
    animation = get_animation_for_damage_type(damage_type, 'attack')
    color = get_color_for_damage_type(damage_type)

    return TurnAction(
        action_id=f"{actor_id}_attack_{datetime.now().microsecond}",
        timestamp=datetime.now(),
        action_type='attack',
        actor_id=actor_id,
        target_id=target_id,
        targets=[target_id],
        amount=damage,
        amounts={target_id: damage},
        damage_type=damage_type,
        is_critical=is_critical,
        animation_name=animation,
        effect_color=color,
        action_name=action_name,
        description=f"{actor_id} attacks {target_id} for {damage} {damage_type or 'generic'} damage{'!' if is_critical else '.'}"
    )


def create_heal_action(
    actor_id: str,
    target_id: str,
    healing: int,
    action_name: str = "Heal"
) -> TurnAction:
    """Create a healing action."""
    return TurnAction(
        action_id=f"{actor_id}_heal_{datetime.now().microsecond}",
        timestamp=datetime.now(),
        action_type='heal',
        actor_id=actor_id,
        target_id=target_id,
        targets=[target_id],
        amount=healing,
        amounts={target_id: healing},
        animation_name='HealOne1.efkefc',
        effect_color='#44FF44',  # Green
        action_name=action_name,
        description=f"{actor_id} heals {target_id} for {healing} HP."
    )


def create_effect_action(
    actor_id: str,
    effect_name: str,
    targets: List[str] = None,
    description: str = ""
) -> TurnAction:
    """Create a status effect action."""
    if targets is None:
        targets = [actor_id]

    # Map common effects to animations
    effect_animations = {
        'burn': 'Fire1.efkefc',
        'poison': 'Poison.efkefc',
        'paralysis': 'Paralyze.efkefc',
        'sleep': 'Sleep.efkefc',
        'confusion': 'Confusion.efkefc',
        'blind': 'Blind.efkefc',
        'silence': 'Silence.efkefc',
        'protection': 'Protection.efkefc',
        'shield': 'Shield.efkefc'
    }

    animation = effect_animations.get(effect_name.lower(), 'HitEffect.efkefc')

    return TurnAction(
        action_id=f"{actor_id}_effect_{datetime.now().microsecond}",
        timestamp=datetime.now(),
        action_type='effect',
        actor_id=actor_id,
        targets=targets,
        animation_name=animation,
        action_name=effect_name,
        description=description or f"{actor_id} applies {effect_name} to {', '.join(targets)}."
    )


def start_battle_recording(run_id: str, battle_id: str) -> BattleRecording:
    """Initialize a new battle recording."""
    recording = BattleRecording(
        battle_id=battle_id,
        run_id=run_id,
        start_time=datetime.now()
    )
    battle_recordings[run_id] = recording

    # Subscribe to battle events to automatically record actions
    _setup_event_handlers(recording)

    return recording


def _setup_event_handlers(recording: BattleRecording) -> None:
    """Setup event handlers to automatically capture battle actions."""

    async def on_damage_dealt(attacker, target, amount, source_type="attack", source_name=None, damage_type=None, **kwargs):
        """Handle damage dealt events."""
        try:
            attacker_id = getattr(attacker, 'id', str(attacker))
            target_id = getattr(target, 'id', str(target))

            # Skip if this is just DoT/HoT ticking (we'll handle those separately)
            if source_type in ('dot', 'hot'):
                return

            # Determine if this is a critical hit based on damage amount
            # This is a heuristic - ideally we'd get this from the damage calculation
            is_critical = amount > (getattr(attacker, 'atk', 0) * 1.5)

            action = create_attack_action(
                actor_id=attacker_id,
                target_id=target_id,
                damage=amount,
                damage_type=damage_type,
                is_critical=is_critical,
                action_name=source_name or "Attack"
            )

            recording.add_action(action)
            log.debug(f"Recorded attack: {attacker_id} -> {target_id} for {amount} {damage_type} damage")

        except Exception as e:
            log.warning(f"Failed to record damage event: {e}")

    async def on_heal(healer, target, amount, source_type="heal", source_name=None, **kwargs):
        """Handle healing events."""
        try:
            healer_id = getattr(healer, 'id', str(healer))
            target_id = getattr(target, 'id', str(target))

            action = create_heal_action(
                actor_id=healer_id,
                target_id=target_id,
                healing=amount,
                action_name=source_name or "Heal"
            )

            recording.add_action(action)
            log.debug(f"Recorded heal: {healer_id} -> {target_id} for {amount} HP")

        except Exception as e:
            log.warning(f"Failed to record heal event: {e}")

    async def on_ultimate_used(caster, target, amount, source_type="ultimate", details=None, **kwargs):
        """Handle ultimate ability events."""
        try:
            caster_id = getattr(caster, 'id', str(caster))
            ultimate_type = details.get('ultimate_type', 'generic') if details else 'generic'

            action = TurnAction(
                action_id=f"{caster_id}_ultimate_{datetime.now().microsecond}",
                timestamp=datetime.now(),
                action_type='ultimate',
                actor_id=caster_id,
                target_id=getattr(target, 'id', None) if target else None,
                damage_type=ultimate_type,
                animation_name=get_animation_for_damage_type(ultimate_type, 'spell'),
                effect_color=get_color_for_damage_type(ultimate_type),
                action_name=f"{ultimate_type.title()} Ultimate",
                description=f"{caster_id} uses their ultimate ability!",
                duration_ms=2000  # Ultimates get longer animations
            )

            recording.add_action(action)
            log.debug(f"Recorded ultimate: {caster_id} uses {ultimate_type} ultimate")

        except Exception as e:
            log.warning(f"Failed to record ultimate event: {e}")

    async def on_entity_killed(victim, killer, amount, source_type="death", details=None, **kwargs):
        """Handle entity death events."""
        try:
            victim_id = getattr(victim, 'id', str(victim))
            killer_id = getattr(killer, 'id', str(killer)) if killer else "Unknown"

            action = TurnAction(
                action_id=f"{victim_id}_death_{datetime.now().microsecond}",
                timestamp=datetime.now(),
                action_type='death',
                actor_id=killer_id,
                target_id=victim_id,
                targets=[victim_id],
                animation_name='Death.efkefc',
                effect_color='#AA0000',  # Dark red
                action_name="Death",
                description=f"{victim_id} has been defeated!",
                duration_ms=1500
            )

            recording.add_action(action)
            log.debug(f"Recorded death: {victim_id} killed by {killer_id}")

        except Exception as e:
            log.warning(f"Failed to record death event: {e}")

    # Subscribe to events
    BUS.subscribe("damage_dealt", on_damage_dealt)
    BUS.subscribe("heal", on_heal)
    BUS.subscribe("ultimate_used", on_ultimate_used)
    BUS.subscribe("entity_killed", on_entity_killed)


def get_battle_recording(run_id: str) -> Optional[BattleRecording]:
    """Get the active battle recording for a run."""
    return battle_recordings.get(run_id)


def end_battle_recording(run_id: str, result: str = 'completed') -> None:
    """Mark a battle recording as complete."""
    recording = battle_recordings.get(run_id)
    if recording:
        recording.is_complete = True
        recording.result = result
        recording.end_time = datetime.now()
        recording.awaiting_frontend = False


def clear_battle_recording(run_id: str) -> None:
    """Remove a battle recording."""
    if run_id in battle_recordings:
        del battle_recordings[run_id]


async def wait_for_frontend_confirmation(run_id: str, timeout_seconds: float = 30.0) -> bool:
    """
    Wait for the frontend to confirm it has finished playing the current action.
    Returns True if confirmed, False if timed out.
    """
    recording = get_battle_recording(run_id)
    if not recording:
        return True  # No recording, don't wait

    if not recording.awaiting_frontend:
        return True  # Not waiting for confirmation

    start_time = asyncio.get_event_loop().time()

    while recording.awaiting_frontend:
        if asyncio.get_event_loop().time() - start_time > timeout_seconds:
            log.warning(f"Frontend confirmation timeout for run {run_id}")
            # Auto-advance on timeout to prevent deadlock
            recording.confirm_action_complete()
            return False

        await asyncio.sleep(0.1)  # Check every 100ms

    return True


def should_use_turn_based_recording(run_id: str) -> bool:
    """
    Check if turn-based recording is enabled for this run.
    This allows gradual rollout of the feature.
    """
    # For now, enable for all new battles
    # Later this could be a user preference or feature flag
    return True
