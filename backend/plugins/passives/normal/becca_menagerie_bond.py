from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar

from autofighter.stat_effect import StatEffect
from autofighter.summons.manager import SummonManager
from plugins.damage_types import load_damage_type

if TYPE_CHECKING:
    from autofighter.party import Party
    from autofighter.stats import Stats


@dataclass
class BeccaMenagerieBond:
    """Becca's Menagerie Bond passive - jellyfish summoning and spirit bonuses."""
    plugin_type = "passive"
    id = "becca_menagerie_bond"
    name = "Menagerie Bond"
    trigger = "action_taken"  # Triggers when Becca acts
    max_stacks = 1  # Only one instance per character
    stack_display = "spinner"

    # Class-level tracking of summon state and spirit bonuses
    _summon_cooldown: ClassVar[dict[str, int]] = {}  # entity_key -> turns_remaining
    _spirit_stacks: ClassVar[dict[str, int]] = {}  # entity_key -> spirit_count
    _last_summon: ClassVar[dict[str, str]] = {}  # entity_key -> last_summon_type
    _applied_spirit_stacks: ClassVar[dict[str, int]] = {}
    _buffed_summons: ClassVar[dict[str, set[int]]] = {}

    # Available jellyfish types
    JELLYFISH_TYPES = ["healing", "electric", "poison", "shielding"]

    @staticmethod
    def _resolve_entity_key(target: "Stats") -> str:
        """Return a stable identifier for tracking Becca's summons."""

        target_id = getattr(target, "id", None)
        if target_id:
            return str(target_id)
        return str(id(target))

    @classmethod
    def _get_summoner_id(cls, target: "Stats") -> str:
        """Return the identifier used by the SummonManager for ``target``."""

        return cls._resolve_entity_key(target)

    async def apply(self, target: "Stats") -> None:
        """Apply Becca's Menagerie Bond mechanics."""
        entity_key = self._resolve_entity_key(target)
        summoner_id = self._get_summoner_id(target)

        if hasattr(target, "ensure_permanent_summon_slots"):
            target.ensure_permanent_summon_slots(1)

        setattr(target, "_becca_menagerie_passive", self)

        # Initialize tracking if not present
        if entity_key not in self._summon_cooldown:
            self._summon_cooldown[entity_key] = 0
            self._spirit_stacks[entity_key] = 0
            self._applied_spirit_stacks[entity_key] = 0
            self._buffed_summons[entity_key] = set()

        current_spirit_stacks = self._spirit_stacks[entity_key]
        applied_stacks = self._applied_spirit_stacks.get(entity_key, 0)

        summons = SummonManager.get_summons(summoner_id)
        jellyfish_summons = [s for s in summons if s.summon_source == self.id]
        current_ids = {id(s) for s in jellyfish_summons}
        buffed_ids = self._buffed_summons.setdefault(entity_key, set())

        spirit_effect_name = f"{self.id}_spirit_bonuses"
        pet_effect_name = f"{self.id}_pet_spirit_bonuses"

        def _has_effect(entity: "Stats", effect_name: str) -> bool:
            if not hasattr(entity, "get_active_effects"):
                return False
            try:
                active_effects = entity.get_active_effects()
            except Exception:
                return False
            return any(effect.name == effect_name for effect in active_effects)

        refresh_required = current_spirit_stacks != applied_stacks
        if current_spirit_stacks > 0 and not _has_effect(target, spirit_effect_name):
            refresh_required = True

        if current_spirit_stacks > 0:
            missing_summon_effects = {
                id(summon)
                for summon in jellyfish_summons
                if not _has_effect(summon, pet_effect_name)
            }
            if missing_summon_effects:
                buffed_ids.difference_update(missing_summon_effects)

        if refresh_required:
            spirit_attack_bonus = int(target._base_atk * 0.05 * current_spirit_stacks)
            spirit_defense_bonus = int(target._base_defense * 0.05 * current_spirit_stacks)

            spirit_effect = StatEffect(
                name=spirit_effect_name,
                stat_modifiers={
                    "atk": spirit_attack_bonus,
                    "defense": spirit_defense_bonus,
                },
                duration=-1,
                source=self.id,
            )
            target.add_effect(spirit_effect)

            for summon in jellyfish_summons:
                pet_effect = StatEffect(
                    name=pet_effect_name,
                    stat_modifiers={
                        "atk": spirit_attack_bonus,
                        "defense": spirit_defense_bonus,
                    },
                    duration=-1,
                    source=self.id,
                )
                summon.add_effect(pet_effect)

            self._applied_spirit_stacks[entity_key] = current_spirit_stacks
            self._buffed_summons[entity_key] = current_ids
        else:
            new_ids = current_ids - buffed_ids
            if new_ids:
                spirit_attack_bonus = int(target._base_atk * 0.05 * current_spirit_stacks)
                spirit_defense_bonus = int(target._base_defense * 0.05 * current_spirit_stacks)
                for summon in jellyfish_summons:
                    if id(summon) in new_ids:
                        pet_effect = StatEffect(
                            name=pet_effect_name,
                            stat_modifiers={
                                "atk": spirit_attack_bonus,
                                "defense": spirit_defense_bonus,
                            },
                            duration=-1,
                            source=self.id,
                        )
                        summon.add_effect(pet_effect)
                buffed_ids.update(new_ids)
            buffed_ids.intersection_update(current_ids)

        # Handle summon cooldown
        if self._summon_cooldown[entity_key] > 0:
            self._summon_cooldown[entity_key] -= 1

    async def on_action_taken(self, target: "Stats", **kwargs) -> None:
        """Attempt to summon a jellyfish when Becca takes an action.

        - Respects internal cooldown and HP cost (handled in summon_jellyfish)
        - Adds the summon to the party immediately if party context is provided
        - Works for foes as well (no party passed); UI still shows foe summons
        """
        party = kwargs.get("party")
        # Accept either a Party object or a raw members list for compatibility
        if party is not None and not hasattr(party, "members"):
            class _PartyShim:
                def __init__(self, members):
                    self.members = members
            party = _PartyShim(party)
        try:
            await self.summon_jellyfish(target, party=party)
        except Exception:
            # Be resilient: summoning failure should not break the turn
            pass

    async def summon_jellyfish(
        self,
        target: "Stats",
        jellyfish_type: str | None = None,
        party: "Party | None" = None,
    ) -> bool:
        """Summon a jellyfish by spending 10% current HP.

        If a ``party`` is provided, the new summon will be appended so it can
        participate in combat immediately.
        """
        entity_key = self._resolve_entity_key(target)
        target_id = self._get_summoner_id(target)

        # Initialize if not present
        if entity_key not in self._summon_cooldown:
            self._summon_cooldown[entity_key] = 0
            self._spirit_stacks[entity_key] = 0

        if hasattr(target, "ensure_permanent_summon_slots"):
            target.ensure_permanent_summon_slots(1)
        if not hasattr(target, "_becca_menagerie_passive"):
            setattr(target, "_becca_menagerie_passive", self)

        # Check cooldown
        if self._summon_cooldown[entity_key] > 0:
            return False

        # Check HP cost (10% of current HP)
        hp_cost = int(target.hp * 0.1)
        if target.hp <= hp_cost:
            return False  # Not enough HP

        # Use the enhanced decision logic from SummonManager
        # But still allow jellyfish type changes (which is Becca's unique mechanic)
        decision = SummonManager.should_resummon(target_id, min_health_threshold=0.3)
        current_summons = SummonManager.get_summons(target_id)
        jellyfish_summons = [s for s in current_summons if s.summon_source == self.id]

        # If a healthy jellyfish exists and no type change is requested, skip summoning
        if jellyfish_summons and not decision["should_resummon"]:
            if jellyfish_type is None or jellyfish_type == self._last_summon.get(entity_key):
                return False

        # Pay HP cost using proper damage system
        target.hp -= hp_cost

        # Select jellyfish type if not specified
        if jellyfish_type is None:
            import random
            jellyfish_type = random.choice(self.JELLYFISH_TYPES)

        # If changing jellyfish type, previous one becomes a spirit
        current_summons = SummonManager.get_summons(target_id)
        jellyfish_summons = [s for s in current_summons if s.summon_source == self.id]

        if jellyfish_summons and jellyfish_type != self._last_summon.get(entity_key):
            # Remove old summon and create spirit
            for old_summon in jellyfish_summons:
                await SummonManager.remove_summon(old_summon, "replaced")
            await self._create_spirit(target)

        # Determine damage type based on jellyfish type
        damage_type = self._get_jellyfish_damage_type(jellyfish_type)

        # Create new summon using summons system
        summon = await SummonManager.create_summon(
            summoner=target,
            summon_type=f"jellyfish_{jellyfish_type}",
            source=self.id,
            stat_multiplier=0.5,  # 50% of Becca's stats as specified
            turns_remaining=-1,  # Permanent until replaced or defeated
            override_damage_type=damage_type,
        )

        if summon:
            if party is not None:
                SummonManager.add_summons_to_party(party)
            self._last_summon[entity_key] = jellyfish_type
            self._summon_cooldown[entity_key] = 1  # One turn cooldown
            return True

        return False

    def _get_jellyfish_damage_type(self, jellyfish_type: str):
        """Get appropriate damage type for jellyfish type."""
        type_mapping = {
            "electric": "Lightning",
            "poison": "Dark",
            "healing": "Light",
            "shielding": "Ice",
        }
        damage_type_name = type_mapping.get(jellyfish_type, "Generic")
        try:
            return load_damage_type(damage_type_name)
        except Exception:
            from plugins.damage_types.generic import Generic
            return Generic()

    async def _create_spirit(self, target: "Stats") -> None:
        """Create a spirit from the previous summon."""
        entity_key = self._resolve_entity_key(target)
        self._spirit_stacks[entity_key] = self._spirit_stacks.get(entity_key, 0) + 1

    async def on_summon_defeat(self, target: "Stats") -> None:
        """Handle summon defeat - still creates a spirit."""
        target_id = self._get_summoner_id(target)

        # Check if any of our jellyfish were defeated
        current_summons = SummonManager.get_summons(target_id)
        jellyfish_summons = [s for s in current_summons if s.summon_source == self.id]

        if not jellyfish_summons:  # Our jellyfish was defeated
            await self._create_spirit(target)

    @classmethod
    def get_active_summon_type(cls, target: "Stats") -> str:
        """Get current active summon type."""
        target_id = cls._get_summoner_id(target)
        summons = SummonManager.get_summons(target_id)
        jellyfish_summons = [s for s in summons if s.summon_source == cls.id]

        if jellyfish_summons:
            summon_type = jellyfish_summons[0].summon_type
            # Extract jellyfish type from summon_type (e.g., "jellyfish_electric" -> "electric")
            if summon_type.startswith("jellyfish_"):
                return summon_type[10:]  # Remove "jellyfish_" prefix

        return None

    @classmethod
    def get_spirit_stacks(cls, target: "Stats") -> int:
        """Get current spirit stack count."""
        return cls._spirit_stacks.get(cls._resolve_entity_key(target), 0)

    @classmethod
    def get_cooldown(cls, target: "Stats") -> int:
        """Get remaining summon cooldown."""
        return cls._summon_cooldown.get(cls._resolve_entity_key(target), 0)

    @classmethod
    def get_last_summon_type(cls, target: "Stats") -> str | None:
        """Return the most recently summoned jellyfish type, if any."""

        return cls._last_summon.get(cls._resolve_entity_key(target))

    @classmethod
    def get_description(cls) -> str:
        return (
            "Spend 10% current HP to summon a jellyfish. "
            "Each former jellyfish leaves a spirit granting +5% attack and defense per stack."
        )
