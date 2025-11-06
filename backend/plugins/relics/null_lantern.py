from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
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
    full_about: str = (
        "Removes all shop and rest rooms from the map. Each battle cleared grants 1 pull token plus "
        "1 additional token per stack. However, enemies grow significantly stronger with each fight: "
        "their ATK, DEF, and Max HP multiply by (1 + 1.5 × battles_cleared × stacks). "
        "This creates an escalating challenge where early battles become easier to clear for pulls, "
        "but later battles become exponentially harder."
    )
    summarized_about: str = (
        "Removes shops and rests; battles grant pull tokens but enemies grow stronger with each fight"
    )

    async def apply(self, party) -> None:
        """Disable shops/rests, buff foes, and award pull tokens."""
        await super().apply(party)

        party.no_shops = True
        party.no_rests = True
        stacks = party.relics.count(self.id)
        state = getattr(party, "_null_lantern_state", None)

        # Get cleared count from persistent state dictionary
        cleared = party.relic_persistent_state.get("null_lantern_cleared", 0)

        if state is None:
            state = {
                "cleared": cleared,
                "stacks": stacks,
                "awarded_in_battle": False,
            }
            party._null_lantern_state = state
        else:
            state["stacks"] = stacks
            state["cleared"] = cleared

        if not hasattr(party, "pull_tokens"):
            party.pull_tokens = 0

        def _is_foe_like(entity) -> bool:
            from plugins.characters.foe_base import FoeBase

            if isinstance(entity, FoeBase):
                return True

            plugin_type = getattr(entity, "plugin_type", "")
            if isinstance(plugin_type, str) and plugin_type.lower() == "foe":
                return True

            rank = getattr(entity, "rank", "")
            if isinstance(rank, str) and "boss" in rank.lower():
                return True

            return False

        async def _battle_start(entity) -> None:
            from plugins.characters.foe_base import FoeBase

            current_state = getattr(party, "_null_lantern_state", state)
            if not _is_foe_like(entity):
                return

            # Reset per-battle award gate for foe-like encounters
            current_state["awarded_in_battle"] = False

            if not isinstance(entity, FoeBase):
                return

            current_stacks = current_state.get("stacks", 0)
            if current_stacks <= 0:
                return
            mult = 1 + 1.5 * current_state["cleared"] * current_stacks
            mgr = getattr(entity, "effect_manager", None)
            if mgr is None:
                mgr = EffectManager(entity)
                entity.effect_manager = mgr

            mod = create_stat_buff(
                entity,
                name=f"{self.id}_foe_{current_state['cleared']}",
                turns=9999,
                atk_mult=mult,
                defense_mult=mult,
                max_hp_mult=mult,
                hp_mult=mult,
            )
            await mgr.add_modifier(mod)

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
            current_state = getattr(party, "_null_lantern_state", state)
            if not _is_foe_like(entity):
                return

            # Ensure we only award once per battle, even with multiple foes
            if current_state.get("awarded_in_battle"):
                return
            current_stacks = current_state.get("stacks", 0)
            if current_stacks <= 0:
                return
            current_state["awarded_in_battle"] = True
            current_state["cleared"] += 1

            # Store in persistent state dictionary
            party.relic_persistent_state["null_lantern_cleared"] = current_state["cleared"]

            pull_reward = 1 + current_stacks

            try:
                current_tokens = int(getattr(party, "pull_tokens", 0) or 0)
            except (TypeError, ValueError):
                current_tokens = 0
            party.pull_tokens = current_tokens + pull_reward

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

    def full_about_stacks(self, stacks: int) -> str:
        """Provide stack-aware description by reusing existing describe logic."""
        return self.describe(stacks)

    def describe(self, stacks: int) -> str:
        pulls = 1 + stacks
        return (
            "Shops and rest rooms vanish. Foes grow stronger each fight; "
            f"each clear grants {pulls} pull{'s' if pulls != 1 else ''}."
        )
