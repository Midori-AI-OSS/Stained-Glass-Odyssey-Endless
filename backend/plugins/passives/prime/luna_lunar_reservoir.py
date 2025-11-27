from dataclasses import dataclass
from math import ceil
from typing import TYPE_CHECKING

from plugins.passives.normal.luna_lunar_reservoir import LunaLunarReservoir

if TYPE_CHECKING:
    from autofighter.stats import Stats


@dataclass
class LunaLunarReservoirPrime(LunaLunarReservoir):
    """Luna's Prime Lunar Reservoir - exalted charge system with massive scaling.

    Prime variant of Luna's passive with 5x charge gains and healing on hits.
    Represents the pinnacle of Luna's power, combining rapid charge accumulation
    with sustain through combat.
    """
    plugin_type = "passive"
    id = "luna_lunar_reservoir_prime"
    name = "Prime Lunar Reservoir"
    trigger = ["action_taken", "ultimate_used", "hit_landed"]
    max_stacks = 2000
    stack_display = "number"

    @classmethod
    def _charge_multiplier(cls, charge_holder: "Stats") -> int:
        """Prime variant has 5x charge multiplier."""
        return 5

    @classmethod
    def _sword_charge_amount(cls, owner: "Stats | None") -> int:
        """Prime variant has 5x sword charge."""
        if owner is None:
            return 0
        return 5  # Base 1 * 5 for prime

    @classmethod
    async def _apply_prime_healing(cls, owner: "Stats", damage: int | None) -> bool:
        """Apply healing based on damage dealt (prime-only feature)."""
        amount = damage or 0
        heal = ceil(amount * 0.000001)
        heal = max(1, min(32, heal))
        await owner.apply_healing(
            heal,
            healer=owner,
            source_type="passive",
            source_name=cls.id,
        )
        return True

    async def apply(self, target: "Stats", event: str = "action_taken", **kwargs: object) -> None:
        """Apply charge mechanics with prime healing."""
        # Call parent apply first
        await super().apply(target, event, **kwargs)

        # Add prime healing on hit_landed
        if event == "hit_landed":
            damage = kwargs.get("damage")
            try:
                damage_value = int(damage)
            except (TypeError, ValueError):
                damage_value = 0
            charge_target = type(self)._resolve_charge_holder(target)
            await self._apply_prime_healing(charge_target, damage_value)

    @classmethod
    async def _on_sword_hit(
        cls,
        owner: "Stats | None",
        sword: "Stats",
        _target,
        amount: int,
        action_type: str,
        metadata: dict | None = None,
    ) -> None:
        """Override to add prime healing on sword hits."""
        # Call parent method first
        await super()._on_sword_hit(owner, sword, _target, amount, action_type, metadata)

        # Add prime healing
        metadata_dict = metadata if isinstance(metadata, dict) else {}
        if not bool(metadata_dict.get("prime_heal_handled")):
            actual_owner = owner
            if owner is None and getattr(sword, "luna_sword_owner", None) is not None:
                actual_owner = getattr(sword, "luna_sword_owner")
            if actual_owner is not None:
                healed = await cls._apply_prime_healing(actual_owner, amount)
                if isinstance(metadata, dict):
                    metadata["prime_heal_handled"] = True
                    metadata["prime_heal_success"] = healed

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Gains 5 charge per action (5x multiplier). "
            "Every 25 charge doubles actions per turn (capped after 2000 doublings). "
            "Stacks above 2000 grant +55% of Luna's base ATK, +1% of her base SPD, "
            "and +1% additional actions from the doubled cadence per 100 excess charge with no automatic drain. "
            "Sword hits grant 5 charge (5x) and heal Luna for a small amount based on damage dealt."
        )

