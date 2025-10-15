from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
import random
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import Collection
from typing import Mapping
import weakref

from autofighter.character import CharacterType
from autofighter.mapgen import MapNode
from autofighter.stats import ANIMATION_OFFSET as _GLOBAL_ANIMATION_OFFSET
from autofighter.stats import BUS
from autofighter.stats import DEFAULT_ANIMATION_DURATION
from autofighter.stats import DEFAULT_ANIMATION_PER_TARGET
from autofighter.summons.base import Summon
from autofighter.summons.manager import SummonManager
from plugins.characters._base import PlayerBase
from plugins.damage_types import ALL_DAMAGE_TYPES
from plugins.damage_types import load_damage_type
from plugins.damage_types._base import DamageTypeBase

if TYPE_CHECKING:
    from autofighter.passives import PassiveRegistry
    from plugins.passives.normal.luna_lunar_reservoir import LunaLunarReservoir


_LUNA_PASSIVE: "type[LunaLunarReservoir] | None" = None

ANIMATION_OFFSET = _GLOBAL_ANIMATION_OFFSET
_DEFAULT_ANIMATION_DURATION = DEFAULT_ANIMATION_DURATION
_DEFAULT_ANIMATION_PER_TARGET = DEFAULT_ANIMATION_PER_TARGET


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
        sword.animation_duration = getattr(
            owner,
            "animation_duration",
            _DEFAULT_ANIMATION_DURATION,
        )
        sword.animation_per_target = getattr(
            owner,
            "animation_per_target",
            _DEFAULT_ANIMATION_PER_TARGET,
        )
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
        passive = _get_luna_passive()
        per_hit = passive._sword_charge_amount(owner)  # type: ignore[attr-defined]
        _register_luna_sword(owner, attacker, label or "")
        passive.add_charge(owner, amount=per_hit)  # type: ignore[attr-defined]
        healed = await passive._apply_prime_healing(owner, amount or 0)  # type: ignore[attr-defined]
        metadata["prime_heal_handled"] = True
        metadata["prime_heal_success"] = healed
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
    looks = """
    Luna Midori is a compact, finely built woman—5′4″, slender and lightly muscled, with the quiet balance of someone who spends as much time reading as she does walking ruin floors. She’s twenty-eight but reads visually as late-teen to early-twenties: youthful face, open gaze, and a softness around the cheeks that never quite goes away even when she’s exhausted. Her skin is pale with a cool undertone, the sort of porcelain that picks up ambient color—blue from moonlight, amber from candles—and she carries a dusting of light freckles across the bridge of her nose and upper cheeks. Her hands are deft and narrow with long fingers; in study scenes they’re ink-smudged and steady, and in the field they sit high on the hilts at her hips with the easy familiarity of practice.
    Her hair is long and loose, a natural dark green that drifts to lighter, mossy tips—thick enough to frame her features in soft, tousled waves. It’s rarely coiffed: sometimes wind-swept in alleys, sometimes haloed by snow in mountain passes, sometimes pushed back beneath the lip of a hood. The color reads as deep forest indoors and picks up sea-glass highlights under cold light. Beneath that fall of hair, her face is heart-shaped with a small, straight nose and a mobile mouth that lives between rueful smiles and intent concentration. Her eyes are the immediate focal point—large, luminous irises of warm gold that catch pinpricks of whatever light is around: candleflame, glyph-glow, or starlit ceilings. They make her look perpetually awake to wonder, even when she’s grieving or guarded.
    Two constant, unmistakable signatures mark her as otherworldly. First: a faint astral halo—silver-gold, thin as a circlet of light—that hovers above her crown. It’s not theatrical; it sits there like a quiet fact, brightening delicately when she’s spell-focused or prayerful. Second: the Vessel of the Twin Veils, a small orb that floats at her right shoulder, trailed by silver-violet wisps like slow candle smoke. It moves as if it understands her, never crowding, simply keeping station—a companionable star at arm’s length.
    Her default clothing is stark and elegant: a loose black strapless evening dress paired with a flowing black hooded cloak. The dress falls in soft, uncomplicated lines to mid-calf, cinched by a practical belt; the cloak carries most of the silhouette, pooling when she sits and catching a clean rim light when she turns. Boots are sturdy and dark under the hem—made for streets and stone, not ballrooms, even when the dress says otherwise. In cold or travel, the cloak’s hood comes up and the whole figure becomes a small moving constellation of black, pale face, and halo.
    She dresses to context without losing herself. On the road or in study, she slips into a travel-stained beige robe bound with a violet-to-rose sash; the colors are muted but read as scholarly and lived-in. In winter scenes she’s swaddled head-to-toe in a heavier, weathered black cloak, the halo a lone bright ring against snowfall. For city errands, she’s been seen in an off-shoulder dark sweater with fitted brown trousers—a practical “I’m just a person” look that still leaves the staff and sidearm visible. And when ceremony calls, she can step into a midnight-blue, star-flecked suit with cape and gem brooch—sleek tailoring that reframes her as a dignitary of the night sky rather than a traveler beneath it.
    Her gear is consistent and personal. Strapped across her back is a golden quarterstaff tipped with a small crystal that throws prismatic color under the right angle; it’s the quiet spine of her silhouette in almost every frame. At her hips ride a matched pair: the Glimmersteel rapier on the left and the Bladeshift dagger on the right, both sheathed, both worn like familiar tools rather than ornament. In study scenes, a blue-covered spellbook glows softly under her hands—she tends to hover a finger over a line before setting it down, as if negotiating with the text. When she carries keepsakes, they’re intimate and purposeful: an amulet she presses to her palm when the world goes wide, and, in sacred places, the cracked Wandering Bauble—a small sphere that glows like a trapped firefly—set on stone as if entrusted to stand watch.
    Luna’s posture and micro-expressions do as much talking as her clothes. On an arcane lift she stands square to the rising light, one hand on the rail, the other at her collarbone—awed, not cowed. In libraries and attic rooms she leans into pages with the listening stillness of someone who knows magic is a conversation. In streets she centers herself quietly, letting the cloak be her privacy without making a scene. In bad weather she tucks into herself and simply endures, the halo a single bright notation above a line of resolve. Overall she reads as small but not fragile—delicate features wrapped around a core of tensile intent. The sum is unmistakable: a starlit scholar-adventurer, equal parts candlelit study and midnight threshold, built more for precision than spectacle, carrying her light with her rather than waiting for the room to provide it.   
    """
    
    ## Help!!! I am stuck in this game!!! Get me out!!
    char_type: CharacterType = CharacterType.B
    damage_type: DamageTypeBase = field(
        default_factory=lambda: load_damage_type("Generic")
    )
    passives: list[str] = field(default_factory=lambda: ["luna_lunar_reservoir"])
    # UI hint: show numeric actions indicator
    actions_display: str = "number"
    animation_duration: float = _DEFAULT_ANIMATION_DURATION
    animation_per_target: float = _DEFAULT_ANIMATION_PER_TARGET
    ultimate_charge_capacity: int = 15_000
    spawn_weight_multiplier: ClassVar[dict[str, float]] = {"non_boss": 5.0}
    music_playlist_weights: ClassVar[dict[str, float]] = {"default": 3.0, "boss": 1.0}

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

        base_weight = super().get_spawn_weight(
            node=node,
            party_ids=party_ids,
            recent_ids=recent_ids,
            boss=boss,
        )
        try:
            weight = float(base_weight)
        except (TypeError, ValueError):
            weight = 1.0

        try:
            floor = int(getattr(node, "floor", 0))
        except Exception:
            floor = 0

        if boss:
            missed = 0
            tracker = getattr(node, "boss_spawn_tracker", None)
            if isinstance(tracker, Mapping):
                history = tracker.get(cls.id)
                if isinstance(history, Mapping):
                    def _safe_int(value: object) -> int | None:
                        try:
                            if value is None:
                                return None
                            return int(value)
                        except Exception:
                            return None

                    current_order = _safe_int(getattr(node, "boss_floor_number", None))
                    if current_order is None:
                        current_order = _safe_int(floor)
                    current_order = max(current_order or 0, 0)

                    last_order = _safe_int(history.get("floor_number"))
                    current_loop = _safe_int(getattr(node, "loop", None))
                    last_loop = _safe_int(history.get("loop"))
                    last_floor = _safe_int(history.get("floor"))
                    current_floor_value = max(_safe_int(floor) or 0, 0)
                    floors_before_current_loop = max(current_order - current_floor_value, 0)

                    if last_order is None and last_floor is not None:
                        if last_loop is None or current_loop is None:
                            last_order = floors_before_current_loop + last_floor if floors_before_current_loop else last_floor
                        elif last_loop == current_loop:
                            last_order = floors_before_current_loop + last_floor
                        else:
                            loops_completed_before_current = max((current_loop or 1) - 1, 0)
                            floors_per_loop = 0
                            if loops_completed_before_current > 0:
                                floors_per_loop = floors_before_current_loop // loops_completed_before_current
                            if floors_per_loop > 0:
                                last_order = max((last_loop - 1) * floors_per_loop + last_floor, 0)

                    if last_order is not None and current_order >= last_order:
                        missed = max(current_order - last_order - 1, 0)
            if missed > 0:
                weight *= pow(2.0, missed)

        if boss and floor % 3 == 0:
            return weight * 6.0
        return weight

    async def prepare_for_battle(
        self,
        node: MapNode,
        registry: "PassiveRegistry",
    ) -> None:
        previous_helper = getattr(self, "_luna_sword_helper", None)
        if isinstance(previous_helper, _LunaSwordCoordinator):
            previous_helper.detach()

        rank = str(getattr(self, "rank", ""))
        lowered = rank.lower()
        is_boss = "boss" in lowered
        is_glitched = "glitched" in lowered

        if not is_boss and not is_glitched:
            self._luna_sword_helper = None
            return

        sword_specs: list[tuple[str, DamageTypeBase]] = []

        if is_glitched and not is_boss:
            sword_count = 2
            self.ensure_permanent_summon_slots(sword_count)
            for _ in range(sword_count):
                damage_label = random.choice(ALL_DAMAGE_TYPES)
                damage_type = load_damage_type(damage_label)
                sword_specs.append(("Lightstream", damage_type))
        else:
            sword_count = 9 if is_glitched else 4
            self.ensure_permanent_summon_slots(sword_count)
            for _ in range(sword_count):
                label = random.choice(ALL_DAMAGE_TYPES)
                damage_type = load_damage_type(label)
                sword_specs.append((label, damage_type))

        helper = _LunaSwordCoordinator(self, registry)
        created = False
        label_counts: dict[str, int] = {}
        for label, damage_type in sword_specs:
            key = label.lower()
            count = label_counts.get(key, 0) + 1
            label_counts[key] = count
            summon_type_base = f"luna_sword_{key}"
            summon_type = summon_type_base if count == 1 else f"{summon_type_base}_{count}"
            summon = await SummonManager.create_summon(
                self,
                summon_type=summon_type,
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

    def apply_boss_scaling(self) -> None:
        rank = str(getattr(self, "rank", ""))
        lowered = rank.lower()
        if "boss" not in lowered:
            return

        multiplier = 11 if "glitched" in lowered else 4
        for stat in ("max_hp", "atk", "defense"):
            base_value = self.get_base_stat(stat)
            try:
                scaled = type(base_value)(base_value * multiplier)
            except Exception:
                continue
            self.set_base_stat(stat, scaled)

        try:
            self.hp = int(self.max_hp)
        except Exception:
            self.hp = self.max_hp
