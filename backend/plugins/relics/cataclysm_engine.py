"""Cataclysm Engine relic implementation."""

from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


def _remove_modifier(entry: tuple[object, object]) -> None:
    """Safely remove a tracked stat modifier."""

    if not entry:
        return
    member, mod = entry
    try:
        mod.remove()
    except Exception:  # pragma: no cover - defensive cleanup
        pass
    mgr = getattr(member, "effect_manager", None)
    if mgr is not None:
        mods = getattr(mgr, "mods", None)
        if mods is not None and mod in mods:
            mods.remove(mod)
    member_mods = getattr(member, "mods", None)
    if isinstance(member_mods, list) and getattr(mod, "id", None) in member_mods:
        member_mods.remove(mod.id)


@dataclass
class CataclysmEngine(RelicBase):
    """Legendary relic that trades HP for overwhelming tempo."""

    id: str = "cataclysm_engine"
    name: str = "Cataclysm Engine"
    stars: int = 5
    effects: dict[str, float] = field(default_factory=dict)
    full_about: str = (
        "Detonates at battle start, sacrificing 15% of all combatants' HP while "
        "boosting ally core stats by 250% and ramping 5% HP drains each turn "
        "with escalating mitigation pulses."
    )
    summarized_about: str = (
        "Trades HP for overwhelming tempo; detonates at battle start to supercharge allies "
        "while bleeding HP each turn for escalating mitigation"
    )

    async def apply(self, party, *, stacks: int | None = None) -> None:
        await super().apply(party, stacks=stacks)

        # Use passed stacks if available, otherwise count (for backward compat)
        if stacks is None:
            stacks = party.relics.count(self.id)
        if stacks <= 0:
            return

        state = getattr(party, "_cataclysm_engine_state", None)
        if state is None:
            state = {
                "mods": {},
                "turn_mods": {},
                "foes": {},
                "activated": False,
                "turn": 0,
                "escalation": 1.0,
            }
            party._cataclysm_engine_state = state
        else:
            for key, entry in list(state.get("turn_mods", {}).items()):
                _remove_modifier(entry)
                state["turn_mods"].pop(key, None)
            for key, entry in list(state.get("mods", {}).items()):
                _remove_modifier(entry)
                state["mods"].pop(key, None)
            state["foes"] = {}
            state["activated"] = False
            state["turn"] = 0
            state["escalation"] = 1.0

        blast_pct = 0.15 + 0.05 * (stacks - 1)
        drain_pct = 0.05 + 0.02 * (stacks - 1)
        per_turn_bonus = max(1.0, 1.0 + 0.05 * stacks)
        core_mult = 2.5 + 0.5 * (stacks - 1)
        defense_mult = 2.0 + 0.4 * (stacks - 1)
        speed_mult = 1.5 + 0.2 * (stacks - 1)
        crit_rate_mult = 1.35 + 0.15 * (stacks - 1)
        crit_damage_mult = 1.5 + 0.2 * (stacks - 1)
        sustain_mult = 1.2 + 0.1 * (stacks - 1)

        state.update(
            {
                "stacks": stacks,
                "blast_pct": blast_pct,
                "drain_pct": drain_pct,
                "per_turn_bonus": per_turn_bonus,
                "core_mult": core_mult,
                "defense_mult": defense_mult,
                "speed_mult": speed_mult,
                "crit_rate_mult": crit_rate_mult,
                "crit_damage_mult": crit_damage_mult,
                "sustain_mult": sustain_mult,
            }
        )

        async def _battle_start(entity) -> None:
            from plugins.characters.foe_base import FoeBase

            current_state = getattr(party, "_cataclysm_engine_state", state)

            if isinstance(entity, FoeBase):
                current_state["foes"][id(entity)] = entity
                damage = max(int(entity.max_hp * current_state["blast_pct"]), 1)
                await BUS.emit_async(
                    "relic_effect",
                    self.id,
                    entity,
                    "foe_cataclysm_blast",
                    damage,
                    {
                        "blast_percentage": current_state["blast_pct"] * 100,
                        "stacks": current_state["stacks"],
                    },
                )
                safe_async_task(entity.apply_cost_damage(damage))
                return

            if current_state.get("activated"):
                return

            current_state["activated"] = True
            current_state["turn"] = 0
            current_state["escalation"] = 1.0

            for member in party.members:
                if getattr(member, "hp", 0) <= 0:
                    continue
                mgr = getattr(member, "effect_manager", None)
                if mgr is None:
                    mgr = EffectManager(member)
                    member.effect_manager = mgr

                mod = create_stat_buff(
                    member,
                    name=f"{self.id}_surge_{id(member)}",
                    turns=9999,
                    atk_mult=current_state["core_mult"],
                    defense_mult=current_state["defense_mult"],
                    spd_mult=current_state["speed_mult"],
                    crit_rate_mult=current_state["crit_rate_mult"],
                    crit_damage_mult=current_state["crit_damage_mult"],
                    mitigation_mult=current_state["sustain_mult"],
                    vitality_mult=current_state["sustain_mult"],
                    max_hp_mult=current_state["sustain_mult"],
                    hp_mult=current_state["sustain_mult"],
                    bypass_diminishing=True,
                )
                await mgr.add_modifier(mod)
                current_state["mods"][id(member)] = (member, mod)

                await BUS.emit_async(
                    "relic_effect",
                    self.id,
                    member,
                    "ally_overclocked",
                    int((current_state["core_mult"] - 1) * 100),
                    {
                        "atk_multiplier": current_state["core_mult"],
                        "defense_multiplier": current_state["defense_mult"],
                        "speed_multiplier": current_state["speed_mult"],
                        "crit_rate_multiplier": current_state["crit_rate_mult"],
                        "crit_damage_multiplier": current_state["crit_damage_mult"],
                        "sustain_multiplier": current_state["sustain_mult"],
                        "stacks": current_state["stacks"],
                    },
                )

                damage = max(int(member.max_hp * current_state["blast_pct"]), 1)
                await BUS.emit_async(
                    "relic_effect",
                    self.id,
                    member,
                    "cataclysm_blast",
                    damage,
                    {
                        "blast_percentage": current_state["blast_pct"] * 100,
                        "stacks": current_state["stacks"],
                    },
                )
                safe_async_task(member.apply_cost_damage(damage))

        async def _turn_start() -> None:
            current_state = getattr(party, "_cataclysm_engine_state", state)
            if not current_state.get("activated"):
                return

            current_state["turn"] += 1
            current_state["escalation"] *= current_state["per_turn_bonus"]

            for key, entry in list(current_state["turn_mods"].items()):
                _remove_modifier(entry)
                current_state["turn_mods"].pop(key, None)

            for member in party.members:
                if getattr(member, "hp", 0) <= 0:
                    continue

                drain = max(int(member.max_hp * current_state["drain_pct"]), 1)
                await BUS.emit_async(
                    "relic_effect",
                    self.id,
                    member,
                    "cataclysm_drain",
                    drain,
                    {
                        "drain_percentage": current_state["drain_pct"] * 100,
                        "turn": current_state["turn"],
                        "escalation_multiplier": current_state["escalation"],
                        "stacks": current_state["stacks"],
                    },
                )
                safe_async_task(member.apply_cost_damage(drain))

                mgr = getattr(member, "effect_manager", None)
                if mgr is None:
                    mgr = EffectManager(member)
                    member.effect_manager = mgr

                mod = create_stat_buff(
                    member,
                    name=f"{self.id}_mitigation_{current_state['turn']}_{id(member)}",
                    turns=1,
                    mitigation_mult=current_state["escalation"],
                    vitality_mult=current_state["escalation"],
                    bypass_diminishing=True,
                )
                await mgr.add_modifier(mod)
                current_state["turn_mods"][id(member)] = (member, mod)

        def _battle_end(entity) -> None:
            from plugins.characters.foe_base import FoeBase

            current_state = getattr(party, "_cataclysm_engine_state", state)
            current_state["foes"].pop(id(entity), None)

            if isinstance(entity, FoeBase) and current_state["foes"]:
                return

            current_state["activated"] = False
            current_state["turn"] = 0
            current_state["escalation"] = 1.0

            for key, entry in list(current_state["turn_mods"].items()):
                _remove_modifier(entry)
                current_state["turn_mods"].pop(key, None)
            for key, entry in list(current_state["mods"].items()):
                _remove_modifier(entry)
                current_state["mods"].pop(key, None)

        self.subscribe(party, "battle_start", _battle_start)
        self.subscribe(party, "turn_start", _turn_start)
        self.subscribe(party, "battle_end", _battle_end)

    def full_about_stacks(self, stacks: int) -> str:
        """Provide stack-aware description by reusing existing describe logic."""
        return self.describe(stacks)

    def describe(self, stacks: int) -> str:
        blast = 15 + 5 * (stacks - 1)
        drain = 5 + 2 * (stacks - 1)
        mult = 250 + 50 * (stacks - 1)
        return (
            f"Detonates at battle start, sacrificing {blast}% of all combatants' HP while "
            f"boosting ally core stats by {mult}% and ramping {drain}% HP drains each turn "
            "with escalating mitigation pulses."
        )
