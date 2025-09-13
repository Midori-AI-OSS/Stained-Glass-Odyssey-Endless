from dataclasses import dataclass
from dataclasses import field

from autofighter.stat_effect import StatEffect
from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class GuardianShard(CardBase):
    id: str = "guardian_shard"
    name: str = "Guardian Shard"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"defense": 0.02, "mitigation": 0.02})
    about: str = "+2% DEF & +2% Mitigation; At battle end, if no allies died, grant +1 small mitigation for the next battle"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        # Track deaths and mitigation bonus
        battle_deaths = 0
        mitigation_bonus_pending = False
        active_members: list = []

        def _on_death(target):
            nonlocal battle_deaths
            # Check if target is one of our party members
            if target in party.members:
                battle_deaths += 1

        def _on_battle_end(target):
            nonlocal mitigation_bonus_pending, active_members

            if target is None:
                return
            if (
                target is not party
                and target not in party.members
                and getattr(target, "plugin_type", None) != "foe"
            ):
                return

            # Remove any active mitigation buffs
            for member in active_members:
                member.remove_effect_by_name(f"{self.id}_mitigation_bonus")
            active_members = []

            # If no allies died, prepare mitigation bonus for next battle
            if battle_deaths == 0:
                mitigation_bonus_pending = True
                import logging
                log = logging.getLogger(__name__)
                log.debug("Guardian Shard mitigation bonus pending for next battle")
                BUS.emit(
                    "card_effect",
                    self.id,
                    None,
                    "guardian_mitigation_pending",
                    1,
                    {
                        "mitigation_bonus": 1,
                        "trigger_condition": "no_deaths",
                        "trigger_event": "battle_end",
                    },
                )

        def _on_battle_start(target):
            nonlocal battle_deaths, mitigation_bonus_pending, active_members
            if target in party.members:
                # Reset death counter for new battle
                battle_deaths = 0

                # Apply pending mitigation bonus if available
                if mitigation_bonus_pending:
                    mitigation_bonus_pending = False
                    active_members = party.members.copy()
                    for member in active_members:
                        # Apply +1 mitigation for this battle
                        member.add_effect(
                            StatEffect(
                                name=f"{self.id}_mitigation_bonus",
                                stat_modifiers={"mitigation": 1},
                                source=self.id,
                            )
                        )
                        import logging
                        log = logging.getLogger(__name__)
                        log.debug(
                            "Guardian Shard mitigation bonus: +1 mitigation to %s",
                            member.id,
                        )
                        BUS.emit(
                            "card_effect",
                            self.id,
                            member,
                            "guardian_mitigation",
                            1,
                            {"mitigation_bonus": 1, "trigger_event": "battle_start"},
                        )

        BUS.subscribe("death", _on_death)
        BUS.subscribe("battle_end", _on_battle_end)
        BUS.subscribe("battle_start", _on_battle_start)
