import asyncio
from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.effects import EffectManager
from autofighter.stats import BUS
from plugins.cards._base import CardBase

log = logging.getLogger(__name__)


@dataclass
class SturdyVest(CardBase):
    id: str = "sturdy_vest"
    name: str = "Sturdy Vest"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"max_hp": 0.03})
    about: str = "+3% HP; When below 35% HP, gain a small 3% HoT for 2 turns"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        # Track active HoTs and remaining turns per member
        active_hots: dict[int, tuple[object, int]] = {}

        async def _check_low_hp(apply_tick: bool = False) -> None:
            # Apply existing HoTs at the start of each turn
            if apply_tick:
                for member_id, (member, turns_left) in list(active_hots.items()):
                    hot_amount = int(getattr(member, "max_hp", 1) * 0.03)

                    async def apply_hot(
                        member: object = member,
                        hot_amount: int = hot_amount,
                    ) -> None:
                        try:
                            await member.apply_healing(
                                hot_amount,
                                source_type="hot",
                                source_name="sturdy_vest",
                            )
                        except Exception as exc:  # pragma: no cover - logging only
                            log.warning("Error applying Sturdy Vest HoT: %s", exc)

                    try:
                        loop = asyncio.get_running_loop()
                    except RuntimeError:
                        asyncio.run(apply_hot())
                    else:
                        loop.create_task(apply_hot())

                    turns_left -= 1
                    if turns_left <= 0:
                        del active_hots[member_id]
                    else:
                        active_hots[member_id] = (member, turns_left)

            # Check for new HoT activations
            for member in party.members:
                member_id = id(member)
                current_hp = getattr(member, "hp", 0)
                max_hp = getattr(member, "max_hp", 1)

                if current_hp / max_hp < 0.35 and member_id not in active_hots:
                    effect_manager = getattr(member, "effect_manager", None)
                    if effect_manager is None:
                        effect_manager = EffectManager(member)
                        member.effect_manager = effect_manager

                    active_hots[member_id] = (member, 2)
                    hot_amount = int(max_hp * 0.03)

                    log.debug(
                        "Sturdy Vest activated HoT for %s: %d HP/turn for 2 turns",
                        member.id,
                        hot_amount,
                    )
                    BUS.emit(
                        "card_effect",
                        self.id,
                        member,
                        "hot_activation",
                        hot_amount,
                        {
                            "hot_amount": hot_amount,
                            "duration": 2,
                            "trigger_threshold": 0.35,
                        },
                    )

        async def _on_turn_start(*_) -> None:
            await _check_low_hp(apply_tick=True)

        async def _on_damage_taken(*_) -> None:
            await _check_low_hp()

        # Check HP at the start of each turn and after damage taken
        BUS.subscribe("turn_start", _on_turn_start)
        BUS.subscribe("damage_taken", _on_damage_taken)
