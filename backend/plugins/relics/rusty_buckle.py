from dataclasses import dataclass
from dataclasses import field
import random

from autofighter.rooms.battle import snapshots as battle_snapshots
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
        "All allies bleed for 5% Max HP per stack at the start of every turn—ally or foe—and unleash Aftertaste as the party suffers."
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

            member_ids = {id(ally) for ally in party.members}
            for key in list(state["prev_hp"].keys()):
                if key not in member_ids:
                    del state["prev_hp"][key]

            for ally in party.members:
                state["prev_hp"][id(ally)] = ally.hp

        def _build_charge_payload() -> list[dict[str, object]] | None:
            current_state = getattr(party, "_rusty_buckle_state", None)
            if not isinstance(current_state, dict):
                return None
            stacks = max(int(current_state.get("stacks", 0)), 0)
            party_max_hp = int(current_state.get("party_max_hp", 0))
            hp_lost = int(current_state.get("hp_lost", 0))
            triggers = max(int(current_state.get("triggers", 0)), 0)
            if stacks <= 0 or party_max_hp <= 0:
                return None
            threshold_multiplier = self._threshold_multiplier(stacks)
            threshold = party_max_hp * threshold_multiplier
            if threshold <= 0:
                progress = 0.0
            else:
                spent = threshold * triggers
                remaining = max(float(hp_lost) - float(spent), 0.0)
                progress = remaining / float(threshold)
            progress = max(0.0, min(progress, 1.0))
            lost_pct = (hp_lost / party_max_hp) if party_max_hp else 0.0
            dmg = int(party_max_hp * lost_pct * 0.005)
            hits = max(0, 5 + 3 * (stacks - 1))
            payload = {
                "id": self.id,
                "name": self.name,
                "stacks": stacks,
                "progress": progress,
                "hp_lost": hp_lost,
                "threshold_per_charge": int(threshold),
                "triggers": triggers,
                "hits": hits,
                "estimated_damage_per_hit": dmg,
                "estimated_total_damage": dmg * hits,
            }
            return [payload]

        def _update_charge_snapshot() -> None:
            run_id = battle_snapshots.resolve_run_id(party)
            if not run_id:
                return
            payload = _build_charge_payload()
            battle_snapshots.set_effect_charges(run_id, payload)

        _update_charge_snapshot()

        async def _turn_start(entity) -> None:
            from plugins.characters._base import PlayerBase
            from plugins.characters.foe_base import FoeBase

            current_state = getattr(party, "_rusty_buckle_state", state)
            if entity is None or not isinstance(entity, (PlayerBase, FoeBase)):
                return
            if isinstance(entity, FoeBase) and entity not in current_state["foes"]:
                current_state["foes"].append(entity)

            current_stacks = current_state.get("stacks", 0)
            if current_stacks <= 0:
                return

            bleed_pct = 0.05 * current_stacks

            for member in party.members:
                if getattr(member, "hp", 0) <= 0:
                    continue

                member_id = id(member)
                current_state["prev_hp"].setdefault(member_id, member.hp)

                bleed = int(member.max_hp * bleed_pct)
                dmg = min(bleed, max(member.hp - 1, 0))
                if dmg <= 0:
                    continue

                await BUS.emit_async(
                    "relic_effect",
                    "rusty_buckle",
                    member,
                    "turn_bleed",
                    dmg,
                    {
                        "target_selection": "each_turn",
                        "bleed_percentage": 5 * current_stacks,
                        "stacks": current_stacks,
                    },
                )

                safe_async_task(member.apply_cost_damage(dmg))

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
            threshold = party_max_hp * self._threshold_multiplier(current_stacks)
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
                        "effect_label": "aftertaste",
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

            _update_charge_snapshot()

        def _heal(target, healer, _amount, *_args) -> None:
            current_state = getattr(party, "_rusty_buckle_state", state)
            if target in party.members:
                current_state["prev_hp"][id(target)] = target.hp
            _update_charge_snapshot()

        def _cleanup(*_args) -> None:
            self.clear_subscriptions(party)
            current_state = getattr(party, "_rusty_buckle_state", None)
            if isinstance(current_state, dict):
                current_state["foes"].clear()
            if current_state is state:
                delattr(party, "_rusty_buckle_state")
            _update_charge_snapshot()

        self.subscribe(party, "turn_start", _turn_start)
        self.subscribe(party, "damage_taken", _damage)
        self.subscribe(party, "heal_received", _heal)
        self.subscribe(party, "battle_end", _cleanup)

    @staticmethod
    def _threshold_multiplier(stacks: int) -> float:
        return 50.0 + 10.0 * max(stacks - 1, 0)

    def describe(self, stacks: int) -> str:
        bleed = 5 * stacks
        hits = 5 + 3 * (stacks - 1)
        req = int(self._threshold_multiplier(stacks) * 100)
        return (
            f"All allies bleed for {bleed}% Max HP at the start of every turn, ally or foe. "
            f"Each {req}% party HP lost (5000% for the first stack and +1000% per extra) triggers {hits} Aftertaste hits at random foes."
        )
