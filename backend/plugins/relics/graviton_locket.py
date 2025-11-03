"""Graviton Locket relic: high-risk battlefield control through gravity debuffs."""

from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase


@dataclass
class GravitonLocket(RelicBase):
    """Cripple enemies with gravity at HP cost to the party."""

    id: str = "graviton_locket"
    name: str = "Graviton Locket"
    stars: int = 4
    effects: dict[str, float] = field(default_factory=dict)
    full_about: str = (
        "On battle start, applies gravity debuff to all enemies reducing SPD by 30% "
        "and increasing damage taken by 12% per stack. Duration: 2 turns +1 per stack. "
        "While any enemy has gravity, party loses 1% Max HP per stack each turn."
    )
    summarized_about: str = (
        "Applies gravity debuff to enemies at battle start; "
        "drains party HP while gravity is active"
    )

    async def apply(self, party) -> None:
        """Apply gravity debuffs to enemies and drain HP while active."""
        await super().apply(party)

        stacks = party.relics.count(self.id)
        spd_reduction = 0.30 * stacks  # 30% SPD reduction per stack
        defense_reduction = 0.12 * stacks  # 12% defense reduction per stack (increases damage taken)
        duration = 2 + stacks  # Base 2 turns + 1 per stack
        hp_drain_pct = 0.01 * stacks  # 1% Max HP per stack

        # Track active gravity modifiers
        state = {"active_debuffs": {}, "mods": []}

        async def _battle_start(entity) -> None:
            """Apply gravity debuff to each enemy at battle start."""
            from plugins.characters.foe_base import FoeBase

            if not isinstance(entity, FoeBase):
                return

            # Create effect manager if needed
            mgr = getattr(entity, "effect_manager", None)
            if mgr is None:
                mgr = EffectManager(entity)
                entity.effect_manager = mgr

            # Apply gravity debuff
            mod = create_stat_buff(
                entity,
                name=f"{self.id}_gravity_{id(entity)}",
                turns=duration,
                spd_mult=1.0 - spd_reduction,
                defense_mult=1.0 - defense_reduction,
            )
            await mgr.add_modifier(mod)
            state["active_debuffs"][id(entity)] = mod
            state["mods"].append(mod)

            # Emit telemetry for gravity application
            await BUS.emit_async(
                "relic_effect",
                self.id,
                entity,
                "gravity_applied",
                int((spd_reduction + defense_reduction) * 100),
                {
                    "target": getattr(entity, "id", str(entity)),
                    "spd_reduction_pct": spd_reduction * 100,
                    "defense_reduction_pct": defense_reduction * 100,
                    "duration_turns": duration,
                    "stacks": stacks,
                },
            )

        async def _turn_start() -> None:
            """Drain HP from party while any enemy has active gravity."""
            # Clean up expired debuffs from tracking
            expired_ids = []
            for entity_id, mod in list(state["active_debuffs"].items()):
                if mod.turns <= 0:
                    expired_ids.append(entity_id)

            for entity_id in expired_ids:
                state["active_debuffs"].pop(entity_id, None)

            # Only drain HP if gravity is still active on any enemy
            if not state["active_debuffs"]:
                return

            # Drain HP from all party members
            for member in party.members:
                dmg = int(member.max_hp * hp_drain_pct)

                # Emit telemetry for HP drain
                await BUS.emit_async(
                    "relic_effect",
                    self.id,
                    member,
                    "hp_drain",
                    dmg,
                    {
                        "drain_percentage": hp_drain_pct * 100,
                        "max_hp": member.max_hp,
                        "active_gravity_count": len(state["active_debuffs"]),
                        "stacks": stacks,
                    },
                )

                await member.apply_cost_damage(dmg)

        def _battle_end(entity) -> None:
            """Clean up all gravity modifiers and state."""
            from plugins.characters.foe_base import FoeBase

            if not isinstance(entity, FoeBase):
                return

            # Only clean up once
            if not state.get("cleaned_up", False):
                # Remove all active modifiers
                for mod in state["mods"]:
                    mod.remove()

                state["active_debuffs"].clear()
                state["mods"].clear()
                state["cleaned_up"] = True
                self.clear_subscriptions(party)

        self.subscribe(party, "battle_start", _battle_start)
        self.subscribe(party, "turn_start", _turn_start)
        self.subscribe(party, "battle_end", _battle_end)

    def full_about_stacks(self, stacks: int) -> str:
        """Provide stack-aware description by reusing existing describe logic."""
        return self.describe(stacks)

    def describe(self, stacks: int) -> str:
        """Generate human-readable description of the relic's effects."""
        spd = 30 * stacks
        dmg_inc = 12 * stacks
        duration = 2 + stacks
        hp = 1 * stacks
        return (
            f"Enemies start battles with -{spd}% SPD and -{dmg_inc}% DEF (increasing damage taken) "
            f"for {duration} turns. While gravity is active, party loses {hp}% Max HP per turn."
        )
