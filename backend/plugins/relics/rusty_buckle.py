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

    async def apply(self, party) -> None:
        """Bleed all allies and ping foes as party HP drops."""
        await super().apply(party)

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
            party._rusty_buckle_state = state
        else:
            state["stacks"] = stacks
            state["party_max_hp"] = sum(ally.max_hp for ally in party.members)
            for ally in party.members:
                state["prev_hp"][id(ally)] = ally.hp

        async def _turn_start(entity) -> None:
            from plugins.foes._base import FoeBase

            current_state = getattr(party, "_rusty_buckle_state", state)
            if isinstance(entity, FoeBase):
                if entity not in current_state["foes"]:
                    current_state["foes"].append(entity)
                return

            if entity in party.members:
                current_stacks = current_state.get("stacks", 0)
                if current_stacks <= 0:
                    return
                bleed = int(entity.max_hp * 0.05 * current_stacks)
                dmg = min(bleed, max(entity.hp - 1, 0))

                await BUS.emit_async(
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

        async def _damage(target, attacker, _original, *_: object) -> None:
            if target not in party.members:
                return
            current_state = getattr(party, "_rusty_buckle_state", state)
            current_stacks = current_state.get("stacks", 0)
            if current_stacks <= 0:
                return
            target_id = id(target)
            prev = current_state["prev_hp"].get(target_id, target.hp)
            lost = max(prev - target.hp, 0)
            current_state["prev_hp"][target_id] = target.hp
            current_state["hp_lost"] += lost
            party_max_hp = current_state["party_max_hp"]
            triggers = current_state["triggers"]
            threshold = party_max_hp * (1 + 0.5 * (current_stacks - 1))
            while party_max_hp and current_state["hp_lost"] >= threshold * (triggers + 1):
                triggers += 1
                current_state["triggers"] = triggers
                lost_pct = current_state["hp_lost"] / party_max_hp
                dmg = int(party_max_hp * lost_pct * 0.005)
                hits = 5 + 3 * (current_stacks - 1)

                await BUS.emit_async(
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
                    if current_state["foes"]:
                        foe = random.choice(current_state["foes"])
                        safe_async_task(Aftertaste(base_pot=dmg).apply(target, foe))

        def _heal(target, healer, _amount, *_args) -> None:
            current_state = getattr(party, "_rusty_buckle_state", state)
            if target in party.members:
                current_state["prev_hp"][id(target)] = target.hp

        def _cleanup(*_args) -> None:
            self.clear_subscriptions(party)
            current_state = getattr(party, "_rusty_buckle_state", None)
            if isinstance(current_state, dict):
                current_state["foes"].clear()
            if current_state is state:
                delattr(party, "_rusty_buckle_state")

        self.subscribe(party, "turn_start", _turn_start)
        self.subscribe(party, "damage_taken", _damage)
        self.subscribe(party, "heal_received", _heal)
        self.subscribe(party, "battle_end", _cleanup)

    def describe(self, stacks: int) -> str:
        bleed = 5 * stacks
        hits = 5 + 3 * (stacks - 1)
        req = int((1 + 0.5 * (stacks - 1)) * 100)
        return (
            f"All allies bleed for {bleed}% Max HP at the start of each turn. "
            f"Each {req}% party HP lost triggers {hits} Aftertaste hits at random foes."
        )
