from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.stats import BUS
from plugins.cards._base import CardBase

log = logging.getLogger(__name__)


@dataclass
class BulwarkTotem(CardBase):
    id: str = "bulwark_totem"
    name: str = "Bulwark Totem"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"defense": 0.02, "max_hp": 0.02})
    about: str = "+2% DEF & +2% HP; When an ally would die, redirect a small percentage of the fatal damage to this unit (tiny soak)"
    damage_share: float = 0.05
    ally_min_health_ratio: float = 0.25

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        async def _on_damage_taken(
            target,
            attacker,
            damage,
            pre_damage_hp=None,
            post_damage_hp=None,
            *_: object,
        ):
            if target not in party.members:
                return

            damage = max(0, int(damage))

            # Determine the HP values before and after the hit.
            if pre_damage_hp is None or post_damage_hp is None:
                post_hit_hp = max(0, int(getattr(target, "hp", 0)))
                pre_hit_hp = post_hit_hp + damage
            else:
                pre_hit_hp = max(0, int(pre_damage_hp))
                post_hit_hp = max(0, int(post_damage_hp))

            max_hp = max(0, int(getattr(target, "max_hp", 0)))

            if pre_hit_hp <= 0:
                return

            # Only trigger on lethal blows where the victim would hit zero HP.
            if post_hit_hp > 0:
                return

            share_ratio = max(0.0, float(self.damage_share))
            if share_ratio <= 0:
                return

            current_hp = max(0, int(getattr(target, "hp", 0)))
            effective_post_hit_hp = max(post_hit_hp, current_hp)

            redirect_amount = max(1, int(damage * share_ratio))

            # Identify a healthy ally that can donate HP.
            healthy_allies = []
            for member in party.members:
                if member is target:
                    continue
                member_hp = max(0, int(getattr(member, "hp", 0)))
                if member_hp <= 0:
                    continue
                member_max_hp = max(1, int(getattr(member, "max_hp", 1)))
                if member_hp / member_max_hp < self.ally_min_health_ratio:
                    continue
                healthy_allies.append(member)

            if not healthy_allies:
                return

            card_holder = max(healthy_allies, key=lambda member: getattr(member, "hp", 0))
            holder_hp = max(0, int(getattr(card_holder, "hp", 0)))
            max_transfer = max(0, holder_hp - 1)
            if max_transfer <= 0:
                return

            heal_cap = max_hp - effective_post_hit_hp if max_hp else redirect_amount
            transfer_amount = min(redirect_amount, max_transfer, heal_cap)
            if transfer_amount <= 0:
                return

            target.hp = (
                effective_post_hit_hp + transfer_amount
                if not max_hp
                else min(effective_post_hit_hp + transfer_amount, max_hp)
            )
            card_holder.hp = max(1, holder_hp - transfer_amount)

            log.debug(
                "Bulwark Totem damage soak: %d damage soaked by %s for %s",
                transfer_amount,
                getattr(card_holder, "id", "unknown"),
                getattr(target, "id", "unknown"),
            )
            await BUS.emit_async(
                "card_effect",
                self.id,
                target,
                "damage_soak",
                transfer_amount,
                {
                    "soak_amount": transfer_amount,
                    "soaker": getattr(card_holder, "id", "unknown"),
                    "protected": getattr(target, "id", "unknown"),
                    "pre_hit_hp": pre_hit_hp,
                    "post_hit_hp": post_hit_hp,
                },
            )

        BUS.subscribe("damage_taken", _on_damage_taken)