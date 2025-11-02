"""Eclipse Reactor relic implementation."""

from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class EclipseReactor(RelicBase):
    """Burst for blood relic: massive surge with lingering drain."""

    id: str = "eclipse_reactor"
    name: str = "Eclipse Reactor"
    stars: int = 5
    effects: dict[str, float] = field(default_factory=dict)
    about: str = (
        "Drains 18% Max HP per stack from each ally at battle start to ignite a 3-turn surge "
        "(+180% ATK, +180% SPD, +60% crit damage per stack). After the surge ends, allies "
        "bleed 2% Max HP per stack every turn until the battle finishes."
    )

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        stacks = party.relics.count(self.id)
        state = getattr(party, "_eclipse_reactor_state", None)
        if state is None:
            state = {
                "mods": {},
                "surge_turns": 0,
                "drain_active": False,
                "surge_active": False,
                "stacks": stacks,
            }
            party._eclipse_reactor_state = state
        else:
            for modifier in list(state.get("mods", {}).values()):
                try:
                    modifier.remove()
                except Exception:
                    pass
            state["mods"] = {}
            state["surge_turns"] = 0
            state["drain_active"] = False
            state["surge_active"] = False
            state["stacks"] = stacks

        async def _battle_start(entity) -> None:
            from plugins.characters.foe_base import FoeBase

            current_state = getattr(party, "_eclipse_reactor_state", state)

            if isinstance(entity, FoeBase):
                return
            if current_state.get("surge_active"):
                return

            current_stacks = party.relics.count(self.id)
            if current_stacks <= 0:
                return

            current_state["surge_active"] = True
            current_state["surge_turns"] = 3
            current_state["drain_active"] = False
            current_state["stacks"] = current_stacks

            surge_atk_mult = 1 + 1.8 * current_stacks
            surge_spd_mult = 1 + 1.8 * current_stacks
            surge_cd_mult = 1 + 0.6 * current_stacks
            drain_pct = 0.02 * current_stacks
            initial_drain_pct = 0.18 * current_stacks

            for member in party.members:
                if getattr(member, "hp", 0) <= 0 or getattr(member, "max_hp", 0) <= 0:
                    continue

                member_id = id(member)
                modifier = current_state["mods"].pop(member_id, None)
                if modifier is not None:
                    try:
                        modifier.remove()
                    except Exception:
                        pass

                hp_before = member.hp
                non_lethal_cap = max(member.hp - 1, 0)
                raw_drain = int(member.max_hp * initial_drain_pct)
                drain_amount = max(0, min(raw_drain, non_lethal_cap))

                await BUS.emit_async(
                    "relic_effect",
                    self.id,
                    member,
                    "initial_hp_drain",
                    drain_amount,
                    {
                        "stacks": current_stacks,
                        "drain_percentage": initial_drain_pct * 100,
                        "hp_before": hp_before,
                        "hp_after": max(hp_before - drain_amount, 0),
                        "non_lethal": True,
                    },
                )

                if drain_amount > 0:
                    safe_async_task(member.apply_cost_damage(drain_amount))

                mgr = getattr(member, "effect_manager", None)
                if mgr is None:
                    mgr = EffectManager(member)
                    member.effect_manager = mgr

                modifier = create_stat_buff(
                    member,
                    name=f"{self.id}_surge_{member_id}",
                    turns=3,
                    atk_mult=surge_atk_mult,
                    spd_mult=surge_spd_mult,
                    crit_damage_mult=surge_cd_mult,
                    bypass_diminishing=True,
                )
                await mgr.add_modifier(modifier)
                current_state["mods"][member_id] = modifier

                await BUS.emit_async(
                    "relic_effect",
                    self.id,
                    member,
                    "surge_activated",
                    int((surge_atk_mult - 1) * 100),
                    {
                        "stacks": current_stacks,
                        "duration_turns": 3,
                        "atk_multiplier": surge_atk_mult,
                        "spd_multiplier": surge_spd_mult,
                        "crit_damage_multiplier": surge_cd_mult,
                    },
                )

        async def _turn_start() -> None:
            current_state = getattr(party, "_eclipse_reactor_state", state)
            if not current_state.get("surge_active"):
                return

            if current_state.get("surge_turns", 0) > 0:
                current_state["surge_turns"] -= 1
                if current_state["surge_turns"] == 0:
                    stacks_active = current_state.get("stacks", 0)
                    drain_pct = 0.02 * stacks_active
                    for member in party.members:
                        member_id = id(member)
                        modifier = current_state.get("mods", {}).pop(member_id, None)
                        if modifier is not None:
                            try:
                                modifier.remove()
                            except Exception:
                                pass
                        if getattr(member, "hp", 0) <= 0:
                            continue
                        await BUS.emit_async(
                            "relic_effect",
                            self.id,
                            member,
                            "surge_expired",
                            0,
                            {
                                "stacks": stacks_active,
                                "post_surge_drain_percentage": drain_pct * 100,
                            },
                        )
                    current_state["drain_active"] = True
                return

            if not current_state.get("drain_active"):
                return

            stacks_active = current_state.get("stacks", 0)
            if stacks_active <= 0:
                return

            drain_pct = 0.02 * stacks_active
            for member in party.members:
                if getattr(member, "hp", 0) <= 0 or getattr(member, "max_hp", 0) <= 0:
                    continue
                damage = int(member.max_hp * drain_pct)

                await BUS.emit_async(
                    "relic_effect",
                    self.id,
                    member,
                    "hp_drain",
                    damage,
                    {
                        "stacks": stacks_active,
                        "drain_percentage": drain_pct * 100,
                        "phase": "post_surge",
                    },
                )

                if damage > 0:
                    safe_async_task(member.apply_cost_damage(damage))

        def _battle_end(entity) -> None:
            from plugins.characters.foe_base import FoeBase

            if not isinstance(entity, FoeBase):
                return

            current_state = getattr(party, "_eclipse_reactor_state", state)
            for modifier in list(current_state.get("mods", {}).values()):
                try:
                    modifier.remove()
                except Exception:
                    pass
            current_state["mods"] = {}
            current_state["surge_turns"] = 0
            current_state["drain_active"] = False
            current_state["surge_active"] = False

        self.subscribe(party, "battle_start", _battle_start)
        self.subscribe(party, "turn_start", _turn_start)
        self.subscribe(party, "battle_end", _battle_end)

    def describe(self, stacks: int) -> str:
        surge_atk = 180 * stacks
        surge_spd = 180 * stacks
        surge_cd = 60 * stacks
        opening_drain = 18 * stacks
        bleed = 2 * stacks
        return (
            f"Battle start drains {opening_drain:.0f}% Max HP per ally to deliver a 3-turn surge "
            f"(+{surge_atk:.0f}% ATK, +{surge_spd:.0f}% SPD, +{surge_cd:.0f}% crit damage). "
            f"Afterward, allies bleed {bleed:.0f}% Max HP each turn until combat ends."
        )
