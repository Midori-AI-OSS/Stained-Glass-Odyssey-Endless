from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase


@dataclass
class NullLantern(RelicBase):
    """Removes shops/rests and converts fights into pulls."""

    id: str = "null_lantern"
    name: str = "Null Lantern"
    stars: int = 4
    effects: dict[str, float] = field(default_factory=dict)
    about: str = "Shops and rest rooms vanish; each fight grants extra pulls."

    async def apply(self, party) -> None:
        """Disable shops/rests, buff foes, and award pull tokens."""
        await super().apply(party)

        party.no_shops = True
        party.no_rests = True
        stacks = party.relics.count(self.id)
        state = getattr(party, "_null_lantern_state", None)
        cleared = getattr(party, "_null_lantern_cleared", 0)

        if state is None:
            state = {
                "cleared": cleared,
                "stacks": stacks,
                "awarded_in_battle": False,
            }
            party._null_lantern_state = state
        else:
            state["stacks"] = stacks

        if not hasattr(party, "pull_tokens"):
            party.pull_tokens = 0

        async def _battle_start(entity) -> None:
            from plugins.characters.foe_base import FoeBase

            current_state = getattr(party, "_null_lantern_state", state)
            if isinstance(entity, FoeBase):
                # Reset per-battle award gate
                current_state["awarded_in_battle"] = False
                current_stacks = current_state.get("stacks", 0)
                if current_stacks <= 0:
                    return
                mult = 1 + 1.5 * current_state["cleared"] * current_stacks
                mod = create_stat_buff(
                    entity,
                    name=f"{self.id}_foe_{current_state['cleared']}",
                    turns=9999,
                    atk_mult=mult,
                    defense_mult=mult,
                    max_hp_mult=mult,
                    hp_mult=mult,
                )
                entity.effect_manager.add_modifier(mod)

                await BUS.emit_async(
                    "relic_effect",
                    "null_lantern",
                    entity,
                    "foe_buffed",
                    int((mult - 1) * 100),
                    {
                        "battle_number": current_state["cleared"] + 1,
                        "multiplier": mult,
                        "escalation_percentage": 150 * current_stacks,
                        "stacks": current_stacks,
                    },
                )

        async def _battle_end(entity) -> None:
            from plugins.characters.foe_base import FoeBase

            current_state = getattr(party, "_null_lantern_state", state)
            if isinstance(entity, FoeBase):
                # Ensure we only award once per battle, even with multiple foes
                if current_state.get("awarded_in_battle"):
                    return
                current_stacks = current_state.get("stacks", 0)
                if current_stacks <= 0:
                    return
                current_state["awarded_in_battle"] = True
                current_state["cleared"] += 1
                party._null_lantern_cleared = current_state["cleared"]
                pull_reward = 1 + current_stacks
                party.pull_tokens += pull_reward

                await BUS.emit_async(
                    "relic_effect",
                    "null_lantern",
                    entity,
                    "pull_tokens_awarded",
                    pull_reward,
                    {
                        "battles_cleared": current_state["cleared"],
                        "base_tokens": 1,
                        "stack_bonus": current_stacks,
                        "disabled_shops": True,
                        "disabled_rests": True,
                    },
                )

        def _cleanup(entity) -> None:
            from plugins.characters.foe_base import FoeBase

            if not isinstance(entity, FoeBase):
                return

            self.clear_subscriptions(party)
            current_state = getattr(party, "_null_lantern_state", None)
            if current_state is state:
                delattr(party, "_null_lantern_state")

        # Keep references for tests to remove if needed
        state["battle_start_handler"] = _battle_start
        state["battle_end_handler"] = _battle_end
        state["cleanup_handler"] = _cleanup

        self.subscribe(party, "battle_start", _battle_start)
        # Award once on either entity_defeat (robust during normal fights)
        # or battle_end (fallback when tests short-circuit kills)
        self.subscribe(party, "entity_defeat", _battle_end)
        self.subscribe(party, "battle_end", _battle_end)
        self.subscribe(party, "battle_end", _cleanup)

    def describe(self, stacks: int) -> str:
        pulls = 1 + stacks
        return (
            "Shops and rest rooms vanish. Foes grow stronger each fight; "
            f"each clear grants {pulls} pull{'s' if pulls != 1 else ''}."
        )
