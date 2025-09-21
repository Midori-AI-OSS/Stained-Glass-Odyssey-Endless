from dataclasses import dataclass
from dataclasses import field
import logging

from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class BattleMeditation(CardBase):
    id: str = "battle_meditation"
    name: str = "Battle Meditation"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"exp_multiplier": 0.03, "vitality": 0.03})
    about: str = "+3% EXP Gain & +3% Vitality; If all allies start at full HP, grant +2% ultimate charge for the first turn"
    _battle_boost_applied: bool = field(default=False, init=False, repr=False)

    def __post_init__(self) -> None:
        super().__post_init__()
        self._battle_boost_applied = False

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        log = logging.getLogger(__name__)

        self._battle_boost_applied = False

        async def _on_battle_start(target):
            if self._battle_boost_applied:
                return

            # Only trigger once per battle when one of our party members starts
            if target in party.members:
                # Check if all allies start at full HP
                all_full_hp = all(
                    getattr(member, 'hp', 0) >= getattr(member, 'max_hp', 1)
                    for member in party.members
                )

                if all_full_hp:
                    self._battle_boost_applied = True
                    # Grant +2 ultimate charge to all party members for first turn
                    for member in party.members:
                        member.add_ultimate_charge(2)
                        log.debug("Battle Meditation ultimate charge bonus: +2 charge to %s", member.id)
                        await BUS.emit_async("card_effect", self.id, member, "meditation_charge", 2, {
                            "charge_bonus": 2,
                            "trigger_condition": "all_full_hp",
                            "trigger_event": "battle_start"
                        })

                    self.unsubscribe("battle_start", _on_battle_start)

        def _on_battle_end(entity) -> None:
            self._battle_boost_applied = False
            self.cleanup_subscriptions()

        self.subscribe("battle_start", _on_battle_start)
        self.subscribe("battle_end", _on_battle_end)
