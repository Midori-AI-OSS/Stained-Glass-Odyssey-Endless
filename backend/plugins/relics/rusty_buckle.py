from dataclasses import dataclass
from dataclasses import field
import random

from autofighter.stats import BUS
from plugins.effects.aftertaste import Aftertaste
from plugins.relics._base import RelicBase
from plugins.relics._base import safe_async_task


@dataclass
class RustyBuckle(RelicBase):
    """Bleeds all allies and triggers Aftertaste as party HP drops."""

    id: str = "rusty_buckle"
    name: str = "Rusty Buckle"
    stars: int = 1
    effects: dict[str, float] = field(default_factory=dict)
    about: str = (
        "All allies bleed for 5% Max HP per stack at the start of each turn and unleash Aftertaste as the party suffers."
    )

    def apply(self, party) -> None:
        """Bleed all allies and ping foes as party HP drops."""
        super().apply(party)

        stacks = party.relics.count(self.id)
        state = getattr(party, "_rusty_buckle_state", None)

        if state is None:
            state = {
                "stacks": stacks,
                "foes": [],
                "party_max_hp": sum(ally.max_hp for ally in party.members),
                "hp_lost": 0,
                "triggers": 0,
                "prev_hp": {id(ally): ally.hp for ally in party.members},
            }

            def _turn_start(entity) -> None:
                from plugins.foes._base import FoeBase

                if isinstance(entity, FoeBase):
                    if entity not in state["foes"]:
                        state["foes"].append(entity)
                    return

                if entity in party.members:
                    current_stacks = state.get("stacks", 0)
                    if current_stacks <= 0:
                        return
                    bleed = int(entity.max_hp * 0.05 * current_stacks)
                    dmg = min(bleed, max(entity.hp - 1, 0))

                    BUS.emit(
                        "relic_effect",
                        "rusty_buckle",
                        entity,
                        "turn_bleed",
                        dmg,
                        {
                            "target_selection": "each_turn",
                            "bleed_percentage": 5 * current_stacks,
                            "stacks": current_stacks,
                        },
                    )

                    safe_async_task(entity.apply_cost_damage(dmg))

            def _damage(target, attacker, _original) -> None:
                if target not in party.members:
                    return
                current_stacks = state.get("stacks", 0)
                if current_stacks <= 0:
                    return
                target_id = id(target)
                prev = state["prev_hp"].get(target_id, target.hp)
                lost = max(prev - target.hp, 0)
                state["prev_hp"][target_id] = target.hp
                state["hp_lost"] += lost
                party_max_hp = state["party_max_hp"]
                triggers = state["triggers"]
                threshold = party_max_hp * (1 + 0.5 * (current_stacks - 1))
                while party_max_hp and state["hp_lost"] >= threshold * (triggers + 1):
                    triggers += 1
                    state["triggers"] = triggers
                    lost_pct = state["hp_lost"] / party_max_hp
                    dmg = int(party_max_hp * lost_pct * 0.005)
                    hits = 5 + 3 * (current_stacks - 1)

                    BUS.emit(
                        "relic_effect",
                        "rusty_buckle",
                        target,
                        "aftertaste_trigger",
                        dmg,
                        {
                            "trigger_count": triggers,
                            "hp_lost_percentage": lost_pct * 100,
                            "aftertaste_hits": hits,
                            "damage_per_hit": dmg,
                        },
                    )

                    for _ in range(hits):
                        if state["foes"]:
                            foe = random.choice(state["foes"])
                            safe_async_task(Aftertaste(base_pot=dmg).apply(target, foe))

            def _heal(target, healer, _amount) -> None:
                if target in party.members:
                    state["prev_hp"][id(target)] = target.hp

            def _cleanup(*_args) -> None:
                BUS.unsubscribe("turn_start", state["turn_start_handler"])
                BUS.unsubscribe("damage_taken", state["damage_handler"])
                BUS.unsubscribe("heal_received", state["heal_handler"])
                BUS.unsubscribe("battle_end", state["cleanup_handler"])
                state["foes"].clear()
                if getattr(party, "_rusty_buckle_state", None) is state:
                    delattr(party, "_rusty_buckle_state")

            state["turn_start_handler"] = _turn_start
            state["damage_handler"] = _damage
            state["heal_handler"] = _heal
            state["cleanup_handler"] = _cleanup
            party._rusty_buckle_state = state

            BUS.subscribe("turn_start", _turn_start)
            BUS.subscribe("damage_taken", _damage)
            BUS.subscribe("heal_received", _heal)
            BUS.subscribe("battle_end", _cleanup)
        else:
            state["stacks"] = stacks
            state["party_max_hp"] = sum(ally.max_hp for ally in party.members)
            for ally in party.members:
                state["prev_hp"][id(ally)] = ally.hp

    def describe(self, stacks: int) -> str:
        bleed = 5 * stacks
        hits = 5 + 3 * (stacks - 1)
        req = int((1 + 0.5 * (stacks - 1)) * 100)
        return (
            f"All allies bleed for {bleed}% Max HP at the start of each turn. "
            f"Each {req}% party HP lost triggers {hits} Aftertaste hits at random foes."
        )
