"""Blood Debt Tithe relic: escalating loot and foe power."""

from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase


@dataclass
class BloodDebtTithe(RelicBase):
    """Trade harder enemies for accelerating rare drop rate growth."""

    id: str = "blood_debt_tithe"
    name: str = "Blood Debt Tithe"
    stars: int = 4
    effects: dict[str, float] = field(default_factory=dict)
    about: str = (
        "Every defeated foe increases the party's rare drop rate for the rest of the run. "
        "Future encounters begin with foes empowered proportionally to the number of "
        "sacrifices already collected (+3% ATK and +2% SPD per stored defeat per stack)."
    )

    async def apply(self, party) -> None:
        """Set up defeat tracking and foe buffing."""
        await super().apply(party)

        stacks = party.relics.count(self.id)

        # Get persistent defeat count from party's relic_persistent_state dictionary
        total_defeats = party.relic_persistent_state.get("blood_debt_tithe_total_defeats", 0)

        # Initialize state tracking
        state = getattr(party, "_blood_debt_tithe_state", None)
        if state is None:
            state = {
                "stacks": stacks,
                "total_defeats": total_defeats,
                "seen_foes_this_battle": set(),
                "foe_buffs": [],
            }
            party._blood_debt_tithe_state = state
        else:
            state["stacks"] = stacks
            state["total_defeats"] = total_defeats

        def _is_foe(entity) -> bool:
            """Check if entity is a foe."""
            from plugins.characters.foe_base import FoeBase

            if isinstance(entity, FoeBase):
                return True

            plugin_type = getattr(entity, "plugin_type", "")
            if isinstance(plugin_type, str) and plugin_type.lower() == "foe":
                return True

            return False

        async def _on_entity_defeat(entity) -> None:
            """Track defeated foes in per-battle set to avoid duplicates."""
            current_state = getattr(party, "_blood_debt_tithe_state", state)

            if not _is_foe(entity):
                return

            # Use entity's id attribute for stable tracking across the battle
            entity_id = getattr(entity, "id", id(entity))
            current_state["seen_foes_this_battle"].add(entity_id)

        async def _on_battle_start(entity) -> None:
            """Apply buff to foes based on stored defeats."""
            from plugins.characters.foe_base import FoeBase

            current_state = getattr(party, "_blood_debt_tithe_state", state)

            if not isinstance(entity, FoeBase):
                return

            current_stacks = current_state.get("stacks", 0)
            total_defeats = current_state.get("total_defeats", 0)

            if current_stacks <= 0 or total_defeats <= 0:
                return

            # Calculate buff: +3% ATK and +2% SPD per defeat per stack
            atk_buff = 1 + (0.03 * total_defeats * current_stacks)
            spd_buff = 1 + (0.02 * total_defeats * current_stacks)

            mgr = getattr(entity, "effect_manager", None)
            if mgr is None:
                mgr = EffectManager(entity)
                entity.effect_manager = mgr

            mod = create_stat_buff(
                entity,
                name=f"{self.id}_foe_{total_defeats}",
                turns=9999,
                atk_mult=atk_buff,
                spd_mult=spd_buff,
            )
            await mgr.add_modifier(mod)
            current_state["foe_buffs"].append(mod)

            await BUS.emit_async(
                "relic_effect",
                "blood_debt_tithe",
                entity,
                "foe_buffed",
                int((atk_buff - 1) * 100),
                {
                    "total_defeats": total_defeats,
                    "atk_multiplier": atk_buff,
                    "spd_multiplier": spd_buff,
                    "atk_percentage": (atk_buff - 1) * 100,
                    "spd_percentage": (spd_buff - 1) * 100,
                    "stacks": current_stacks,
                },
            )

        async def _on_battle_end(entity) -> None:
            """Bank unique defeats and increase party RDR."""
            from plugins.characters.foe_base import FoeBase

            current_state = getattr(party, "_blood_debt_tithe_state", state)

            # Only process when a foe's battle ends
            if not isinstance(entity, FoeBase):
                return

            # Skip if we've already processed this battle (using a flag)
            if current_state.get("processed_this_battle", False):
                return

            # Mark as processed for this battle
            current_state["processed_this_battle"] = True

            current_stacks = current_state.get("stacks", 0)
            if current_stacks <= 0:
                current_state["seen_foes_this_battle"].clear()
                return

            # Count unique defeats in this battle
            new_defeats = len(current_state["seen_foes_this_battle"])
            if new_defeats <= 0:
                return

            # Update total defeats in both state and persistent party dictionary
            current_state["total_defeats"] += new_defeats
            party.relic_persistent_state["blood_debt_tithe_total_defeats"] = current_state["total_defeats"]

            # Increase rare drop rate: 0.2 percentage points per stack per defeat
            rdr_increase = 0.002 * current_stacks * new_defeats
            party.rdr += rdr_increase

            await BUS.emit_async(
                "relic_effect",
                "blood_debt_tithe",
                party,
                "defeats_banked",
                new_defeats,
                {
                    "new_defeats": new_defeats,
                    "total_defeats": current_state["total_defeats"],
                    "rdr_increase": rdr_increase * 100,
                    "rdr_increase_percentage_points": rdr_increase * 100,
                    "current_rdr": party.rdr,
                    "stacks": current_stacks,
                },
            )

        def _cleanup(*_args, **_kwargs) -> None:
            """Clean up per-battle state and foe buffs."""
            current_state = getattr(party, "_blood_debt_tithe_state", None)
            if current_state is None:
                return

            # Clear per-battle tracking
            current_state["seen_foes_this_battle"].clear()
            current_state["processed_this_battle"] = False

            # Remove foe buffs
            for mod in current_state.get("foe_buffs", []):
                try:
                    mod.remove()
                except Exception:
                    pass
            current_state["foe_buffs"].clear()

        self.subscribe(party, "entity_defeat", _on_entity_defeat)
        self.subscribe(party, "battle_start", _on_battle_start)
        self.subscribe(party, "battle_end", _on_battle_end)
        self.subscribe(party, "battle_end", _cleanup)

    def describe(self, stacks: int) -> str:
        """Return a stack-aware description."""
        atk_per_defeat = 3 * stacks
        spd_per_defeat = 2 * stacks
        rdr_per_defeat = 0.2 * stacks
        return (
            f"Each defeated foe grants +{rdr_per_defeat:.1f}% rare drop rate. "
            f"Future foes gain +{atk_per_defeat}% ATK and +{spd_per_defeat}% SPD per stored defeat."
        )
