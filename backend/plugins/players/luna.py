from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
import random
from typing import TYPE_CHECKING
from typing import Collection
import weakref

from autofighter.character import CharacterType
from autofighter.mapgen import MapNode
from autofighter.stats import BUS
from autofighter.summons.base import Summon
from autofighter.summons.manager import SummonManager
from plugins.damage_types import ALL_DAMAGE_TYPES
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase
from plugins.players._base import PlayerBase

if TYPE_CHECKING:
    from autofighter.passives import PassiveRegistry
    from plugins.passives.normal.luna_lunar_reservoir import LunaLunarReservoir


_LUNA_PASSIVE: "type[LunaLunarReservoir] | None" = None


def _get_luna_passive() -> "type[LunaLunarReservoir]":
    """Import Luna's passive lazily to avoid circular dependencies."""

    global _LUNA_PASSIVE
    if _LUNA_PASSIVE is None:
        from plugins.passives.normal.luna_lunar_reservoir import LunaLunarReservoir

        _LUNA_PASSIVE = LunaLunarReservoir
    return _LUNA_PASSIVE


def _register_luna_sword(owner: "Luna", sword: Summon, label: str) -> None:
    """Register a sword with Luna's passive without leaking import cycles."""

    passive = _get_luna_passive()
    passive._ensure_event_hooks()  # type: ignore[attr-defined]
    passive._ensure_charge_slot(owner)  # type: ignore[attr-defined]
    owner_id = id(passive._resolve_charge_holder(owner))  # type: ignore[attr-defined]
    passive._swords_by_owner.setdefault(owner_id, set()).add(id(sword))  # type: ignore[attr-defined]
    if isinstance(label, str):
        setattr(sword, "luna_sword_label", label)


class _LunaSwordCoordinator:
    """Manage Luna's summoned swords within a single battle."""

    EVENT_NAME = "luna_sword_hit"

    def __init__(self, owner: "Luna", _registry: "PassiveRegistry") -> None:
        self._owner_ref: weakref.ReferenceType[Luna] = weakref.ref(owner)
        self._sword_refs: dict[int, weakref.ReferenceType[Summon]] = {}
        self._hit_listener = self._handle_hit
        self._removal_listener = self._handle_removal
        BUS.subscribe("hit_landed", self._hit_listener)
        BUS.subscribe("summon_removed", self._removal_listener)

    def add_sword(self, sword: Summon, label: str) -> None:
        """Track a newly created sword and tag it for downstream systems."""

        owner = self._owner_ref()
        if owner is None:
            return
        self._sword_refs[id(sword)] = weakref.ref(sword)
        sword.actions_per_turn = owner.actions_per_turn
        sword.summon_type = f"luna_sword_{label.lower()}"
        sword.summon_source = "luna_sword"
        sword.is_temporary = False
        tags = set(getattr(sword, "tags", set()))
        tags.update({"luna", "sword", label.lower()})
        sword.tags = tags
        sword.luna_sword_label = label
        sword.luna_sword_owner_id = getattr(owner, "id", None)
        sword.luna_sword = True
        sword.luna_sword_owner = owner
        _register_luna_sword(owner, sword, label)

    def sync_actions_per_turn(self) -> None:
        """Mirror the owner's action cadence onto all tracked swords."""

        owner = self._owner_ref()
        if owner is None:
            return
        actions = owner.actions_per_turn
        for sword_ref in list(self._sword_refs.values()):
            sword = sword_ref()
            if sword is None:
                continue
            sword.actions_per_turn = actions

    async def _handle_hit(
        self,
        attacker: Summon | None,
        target,
        amount: int | None = None,
        action_type: str | None = None,
        identifier: str | None = None,
        *_: object,
    ) -> None:
        """Re-broadcast sword hits so Luna's passives can respond."""

        if attacker is None or id(attacker) not in self._sword_refs:
            return
        owner = self._owner_ref()
        if owner is None:
            self.detach()
            return
        label = getattr(attacker, "luna_sword_label", None)
        metadata = {
            "sword_label": label,
            "sword_identifier": getattr(attacker, "id", None),
            "source_identifier": identifier,
        }
        per_hit = 4
        rank = str(getattr(owner, "rank", ""))
        if "glitched" in rank.lower():
            per_hit = 8
        _register_luna_sword(owner, attacker, label or "")
        passive = _get_luna_passive()
        passive.add_charge(owner, amount=per_hit)  # type: ignore[attr-defined]
        try:
            helper = getattr(owner, "_luna_sword_helper", None)
            if helper is not None and hasattr(helper, "sync_actions_per_turn"):
                helper.sync_actions_per_turn()
        except Exception:
            pass
        metadata["charge_handled"] = True
        await BUS.emit_async(
            self.EVENT_NAME,
            owner,
            attacker,
            target,
            amount or 0,
            action_type or "attack",
            metadata,
        )

    def _handle_removal(self, summon: Summon | None, *_: object) -> None:
        """Drop tracking when a sword is despawned."""

        if summon is None:
            return
        sid = id(summon)
        if sid not in self._sword_refs:
            return
        self._sword_refs.pop(sid, None)
        _get_luna_passive().unregister_sword(summon)
        if not self._sword_refs:
            self.detach()

    def detach(self) -> None:
        """Unsubscribe from event bus callbacks when swords are gone."""
        for sword_ref in list(self._sword_refs.values()):
            sword = sword_ref()
            if sword is not None:
                _get_luna_passive().unregister_sword(sword)
        self._sword_refs.clear()
        BUS.unsubscribe("hit_landed", self._hit_listener)
        BUS.unsubscribe("summon_removed", self._removal_listener)



@dataclass
class Luna(PlayerBase):
    id = "luna"
    name = "Luna"
    about = "Luna Midori fights like a stargazer who mapped the constellations of violence—quiet, exact, always a beat ahead. Her thin astral halo brightens as she sketches unseen wards; the Vessel of the Twin Veils keeps station at her shoulder, flaring to tip arrows off-line. She opens by controlling the field: silvery pressure that anchors feet, a hush that snuffs a spell mid-syllable, a ripple that leaves an after-image where she stood. When steel is required, the Glimmersteel rapier writes quick, grammatical cuts, the golden quarterstaff sets the tempo and distance, and the Bladeshift dagger ends what hesitation begins. She moves light and economical—cloak skimming stone, angles over brute force—talking just enough to knock an enemy off rhythm. Her magic is moon-cold and precise: starlight darts, gravity tugs, the soft collapse of air before a controlled blast—never wasteful, always aimed at the lever that topples the fight. She isn't a brawler; she's a clockmaker in a storm, turning the right gear until the whole field ticks her way."
    ##
    char_type: CharacterType = CharacterType.B
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type("Generic")
    )
    passives: list[str] = field(default_factory=lambda: ["luna_lunar_reservoir"])
    # UI hint: show numeric actions indicator
    actions_display: str = "number"

    @classmethod
    def get_spawn_weight(
        cls,
        *,
        node: MapNode,
        party_ids: Collection[str],
        recent_ids: Collection[str] | None = None,
        boss: bool = False,
    ) -> float:
        if cls.id in {str(pid) for pid in party_ids}:
            return 0.0

        try:
            floor = int(getattr(node, "floor", 0))
        except Exception:
            floor = 0

        if boss and floor % 3 == 0:
            return 6.0
        return 1.0

    def prepare_for_battle(
        self,
        node: MapNode,
        registry: "PassiveRegistry",
    ) -> None:
        previous_helper = getattr(self, "_luna_sword_helper", None)
        if isinstance(previous_helper, _LunaSwordCoordinator):
            previous_helper.detach()

        rank = str(getattr(self, "rank", ""))
        if "boss" not in rank.lower():
            self._luna_sword_helper = None
            return

        sword_count = 9 if "glitched" in rank.lower() else 4
        self.ensure_permanent_summon_slots(sword_count)

        helper = _LunaSwordCoordinator(self, registry)
        created = False
        for _ in range(sword_count):
            label = random.choice(ALL_DAMAGE_TYPES)
            damage_type = load_damage_type(label)
            summon = SummonManager.create_summon(
                self,
                summon_type=f"luna_sword_{label.lower()}",
                source="luna_sword",
                stat_multiplier=1.0,
                override_damage_type=damage_type,
                force_create=True,
            )
            if summon is None:
                continue
            created = True
            summon.owner_ref = weakref.ref(self)
            helper.add_sword(summon, label)
            _register_luna_sword(self, summon, label)

        if not created:
            helper.detach()
            self._luna_sword_helper = None
            return

        helper.sync_actions_per_turn()
        self._luna_sword_helper = helper
