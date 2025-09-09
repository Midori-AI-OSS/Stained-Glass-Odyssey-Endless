from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import ClassVar

from autofighter.stats import StatEffect
from autofighter.summons import SummonManager
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
    _summon_cooldown: ClassVar[dict[int, int]] = {}  # entity_id -> turns_remaining
    _spirit_stacks: ClassVar[dict[int, int]] = {}  # entity_id -> spirit_count
    _last_summon: ClassVar[dict[int, str]] = {}  # entity_id -> last_summon_type
    _applied_spirit_stacks: ClassVar[dict[int, int]] = {}
    _buffed_summons: ClassVar[dict[int, set[int]]] = {}

    # Available jellyfish types
    JELLYFISH_TYPES = ["healing", "electric", "poison", "shielding"]

    async def apply(self, target: "Stats") -> None:
        """Apply Becca's Menagerie Bond mechanics."""
        entity_id = id(target)

        # Initialize tracking if not present
        if entity_id not in self._summon_cooldown:
            self._summon_cooldown[entity_id] = 0
            self._spirit_stacks[entity_id] = 0
            self._applied_spirit_stacks[entity_id] = 0
            self._buffed_summons[entity_id] = set()

        current_spirit_stacks = self._spirit_stacks[entity_id]
        applied_stacks = self._applied_spirit_stacks.get(entity_id, 0)

        summons = SummonManager.get_summons(getattr(target, "id", str(id(target))))
        jellyfish_summons = [s for s in summons if s.summon_source == self.id]
        current_ids = {id(s) for s in jellyfish_summons}
        buffed_ids = self._buffed_summons.setdefault(entity_id, set())

        if current_spirit_stacks != applied_stacks:
            spirit_attack_bonus = int(target._base_atk * 0.05 * current_spirit_stacks)
            spirit_defense_bonus = int(
                target._base_defense * 0.05 * current_spirit_stacks
            )

            spirit_effect = StatEffect(
                name=f"{self.id}_spirit_bonuses",
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
                    name=f"{self.id}_pet_spirit_bonuses",
                    stat_modifiers={
                        "atk": spirit_attack_bonus,
                        "defense": spirit_defense_bonus,
                    },
                    duration=-1,
                    source=self.id,
                )
                summon.add_effect(pet_effect)

            self._applied_spirit_stacks[entity_id] = current_spirit_stacks
            self._buffed_summons[entity_id] = current_ids
        else:
            new_ids = current_ids - buffed_ids
            if new_ids:
                spirit_attack_bonus = int(
                    target._base_atk * 0.05 * current_spirit_stacks
                )
                spirit_defense_bonus = int(
                    target._base_defense * 0.05 * current_spirit_stacks
                )
                for summon in jellyfish_summons:
                    if id(summon) in new_ids:
                        pet_effect = StatEffect(
                            name=f"{self.id}_pet_spirit_bonuses",
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
        if self._summon_cooldown[entity_id] > 0:
            self._summon_cooldown[entity_id] -= 1

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
        entity_id = id(target)
        target_id = getattr(target, "id", str(id(target)))

        # Initialize if not present
        if entity_id not in self._summon_cooldown:
            self._summon_cooldown[entity_id] = 0
            self._spirit_stacks[entity_id] = 0

        # Check cooldown
        if self._summon_cooldown[entity_id] > 0:
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

        # If we have viable jellyfish and we're not changing type, skip summoning
        if (
            not decision["should_resummon"]
            and jellyfish_type == self._last_summon.get(entity_id)
            and jellyfish_summons
        ):
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

        if jellyfish_summons and jellyfish_type != self._last_summon.get(entity_id):
            # Remove old summon and create spirit
            for old_summon in jellyfish_summons:
                SummonManager.remove_summon(old_summon, "replaced")
            await self._create_spirit(target)

        # Determine damage type based on jellyfish type
        damage_type = self._get_jellyfish_damage_type(jellyfish_type)

        # Create new summon using summons system
        summon = SummonManager.create_summon(
            summoner=target,
            summon_type=f"jellyfish_{jellyfish_type}",
            source=self.id,
            stat_multiplier=0.5,  # 50% of Becca's stats as specified
            turns_remaining=-1,  # Permanent until replaced or defeated
            override_damage_type=damage_type,
            max_summons=1,  # Only one jellyfish at a time
        )

        if summon:
            if party is not None:
                SummonManager.add_summons_to_party(party)
            self._last_summon[entity_id] = jellyfish_type
            self._summon_cooldown[entity_id] = 1  # One turn cooldown
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
        entity_id = id(target)
        self._spirit_stacks[entity_id] += 1

    async def on_summon_defeat(self, target: "Stats") -> None:
        """Handle summon defeat - still creates a spirit."""
        target_id = getattr(target, "id", str(id(target)))

        # Check if any of our jellyfish were defeated
        current_summons = SummonManager.get_summons(target_id)
        jellyfish_summons = [s for s in current_summons if s.summon_source == self.id]

        if not jellyfish_summons:  # Our jellyfish was defeated
            await self._create_spirit(target)

    @classmethod
    def get_active_summon_type(cls, target: "Stats") -> str:
        """Get current active summon type."""
        target_id = getattr(target, "id", str(id(target)))
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
        return cls._spirit_stacks.get(id(target), 0)

    @classmethod
    def get_cooldown(cls, target: "Stats") -> int:
        """Get remaining summon cooldown."""
        return cls._summon_cooldown.get(id(target), 0)

    @classmethod
    def get_description(cls) -> str:
        return (
            "Spend 10% current HP to summon a jellyfish. "
            "Each former jellyfish leaves a spirit granting +5% attack and defense per stack."
        )
