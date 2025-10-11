from dataclasses import dataclass
from dataclasses import field

from autofighter.stats import BUS
from plugins.cards._base import CardBase


@dataclass
class EnduringWill(CardBase):
    id: str = "enduring_will"
    name: str = "Enduring Will"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=lambda: {"mitigation": 0.03, "vitality": 0.03})
    about: str = "+3% Mitigation & +3% Vitality; If no allies die during combat, grant +0.2% mitigation next battle"

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        # Track deaths and mitigation bonus
        battle_deaths = 0
        mitigation_bonus_pending = False

        def _on_death(target):
            nonlocal battle_deaths
            # Check if target is one of our party members
            if target in party.members:
                battle_deaths += 1

        async def _on_battle_end():
            nonlocal mitigation_bonus_pending
            # If no allies died, prepare mitigation bonus for next battle
            if battle_deaths == 0:
                mitigation_bonus_pending = True
                import logging
                log = logging.getLogger(__name__)
                log.debug("Enduring Will mitigation bonus pending for next battle")
                await BUS.emit_async("card_effect", self.id, None, "mitigation_bonus_pending", 1, {
                    "mitigation_bonus": 1,
                    "trigger_condition": "no_deaths",
                    "trigger_event": "battle_end"
                })

        async def _on_battle_start(target):
            nonlocal battle_deaths, mitigation_bonus_pending
            if target in party.members:
                # Reset death counter for new battle
                battle_deaths = 0

                # Apply pending mitigation bonus if available
                if mitigation_bonus_pending:
                    mitigation_bonus_pending = False
                    for member in party.members:
                        # Apply +0.002 mitigation (0.2% - small bonus appropriate for 1-star card)
                        from autofighter.effects import EffectManager
                        from autofighter.effects import create_stat_buff
                        mgr = getattr(member, "effect_manager", None)
                        if mgr is None:
                            mgr = EffectManager(member)
                            member.effect_manager = mgr

                        # Create temporary mitigation buff for this battle
                        mod = create_stat_buff(
                            member, name=f"{self.id}_mitigation_bonus", turns=20,
                            mitigation_mult=1.002  # +0.2% mitigation
                        )
                        await mgr.add_modifier(mod)

                        import logging
                        log = logging.getLogger(__name__)
                        log.debug("Enduring Will mitigation bonus: +0.002 mitigation to %s", member.id)
                        await BUS.emit_async("card_effect", self.id, member, "mitigation_bonus", 0.002, {
                            "mitigation_bonus": 0.002,
                            "trigger_event": "battle_start"
                        })

        self.subscribe("death", _on_death)
        self.subscribe("battle_end", _on_battle_end)
        self.subscribe("battle_start", _on_battle_start)
