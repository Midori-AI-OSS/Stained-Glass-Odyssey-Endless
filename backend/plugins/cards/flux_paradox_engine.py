from dataclasses import dataclass
from dataclasses import field

from autofighter.effects import EffectManager
from autofighter.effects import create_stat_buff
from autofighter.stats import BUS
from plugins.cards._base import CardBase
from plugins.dots.blazing_torment import BlazingTorment
from plugins.dots.cold_wound import ColdWound


@dataclass
class FluxParadoxEngine(CardBase):
    id: str = "flux_paradox_engine"
    name: str = "Flux Paradox Engine"
    stars: int = 4
    effects: dict[str, float] = field(
        default_factory=lambda: {
            "effect_hit_rate": 2.40,
            "effect_resistance": 2.40,
        }
    )
    about: str = (
        "+240% Effect Hit Rate & +240% Effect Resistance; alternates Fire and Ice stances "
        "each turn. Fire stance: the first damaging action each ally takes applies "
        "Blazing Torment to its target. Ice stance: the first damaging action each ally "
        "takes applies Cold Wound and grants +12% Mitigation for 1 turn."
    )

    async def apply(self, party) -> None:  # type: ignore[override]
        await super().apply(party)

        state_store = getattr(party, "_flux_paradox_engine_state", None)
        if state_store is None:
            state_store = {}
            party._flux_paradox_engine_state = state_store

        if state_store.get(self.id):
            return

        state: dict[str, object] = {
            "turn_index": 0,
            "mode": "Fire",
            "triggered": set(),
            "foes": {},
            "battle_active": False,
        }
        state_store[self.id] = state

        def _members_match(entity) -> bool:
            return any(entity is member for member in getattr(party, "members", ()))

        async def _battle_start(entity) -> None:
            if entity is None:
                return
            if _members_match(entity):
                if not state["battle_active"]:
                    state["battle_active"] = True
                    state["turn_index"] = 0
                    state["mode"] = "Fire"
                    triggered = state.get("triggered")
                    if isinstance(triggered, set):
                        triggered.clear()
                    foes = state.get("foes")
                    if isinstance(foes, dict):
                        foes.clear()
                return

            foes = state.get("foes")
            if isinstance(foes, dict):
                foes[id(entity)] = entity

        async def _battle_end(entity) -> None:
            if entity is None or entity is party or _members_match(entity):
                state["battle_active"] = False
                state["turn_index"] = 0
                state["mode"] = "Fire"
                triggered = state.get("triggered")
                if isinstance(triggered, set):
                    triggered.clear()
                foes = state.get("foes")
                if isinstance(foes, dict):
                    foes.clear()
                state_store.pop(self.id, None)
                if not state_store:
                    try:
                        delattr(party, "_flux_paradox_engine_state")
                    except AttributeError:
                        pass
                return

            foes = state.get("foes")
            if isinstance(foes, dict):
                foes.pop(id(entity), None)

        async def _turn_start(actor=None, *_args) -> None:
            if not state.get("battle_active"):
                return
            state["turn_index"] = int(state.get("turn_index", 0)) + 1
            turn_index = int(state["turn_index"])
            mode = "Fire" if turn_index % 2 == 1 else "Ice"
            state["mode"] = mode
            triggered = state.get("triggered")
            if isinstance(triggered, set):
                triggered.clear()
            await BUS.emit_async(
                "card_effect",
                self.id,
                actor,
                "stance_shift",
                turn_index,
                {
                    "mode": mode,
                    "turn_index": turn_index,
                    "actor_id": getattr(actor, "id", None),
                },
            )

        async def _hit_landed(attacker, target, amount, *_extra) -> None:
            if not state.get("battle_active"):
                return
            if attacker is None or target is None:
                return
            if not _members_match(attacker):
                return
            if getattr(target, "hp", 0) <= 0:
                return
            if amount is None or amount <= 0:
                return

            triggered = state.get("triggered")
            if not isinstance(triggered, set):
                return
            key = id(attacker)
            if key in triggered:
                return

            triggered.add(key)
            mode = state.get("mode", "Fire")

            mgr = getattr(target, "effect_manager", None)
            if mgr is None:
                mgr = EffectManager(target)
                target.effect_manager = mgr

            applied_amount = 0
            event_name = ""

            if mode == "Ice":
                dot_damage = max(1, int(amount * 0.4))
                cold = ColdWound(dot_damage, 3)
                cold.source = attacker
                await mgr.add_dot(cold, max_stacks=getattr(ColdWound, "max_stacks", None))
                applied_amount = dot_damage
                event_name = "ice_stance_dot"

                attacker_mgr = getattr(attacker, "effect_manager", None)
                if attacker_mgr is None:
                    attacker_mgr = EffectManager(attacker)
                    attacker.effect_manager = attacker_mgr
                mitigation = create_stat_buff(
                    attacker,
                    name=f"{self.id}_mitigation",
                    turns=1,
                    mitigation_mult=1.12,
                )
                await attacker_mgr.add_modifier(mitigation)
            else:
                dot_damage = max(1, int(amount * 0.5))
                burn = BlazingTorment(dot_damage, 3)
                burn.source = attacker
                await mgr.add_dot(burn)
                applied_amount = dot_damage
                event_name = "fire_stance_dot"

            await BUS.emit_async(
                "card_effect",
                self.id,
                attacker,
                event_name,
                applied_amount,
                {
                    "mode": mode,
                    "target_id": getattr(target, "id", None),
                    "attacker_id": getattr(attacker, "id", None),
                },
            )

        self.subscribe("battle_start", _battle_start)
        self.subscribe("battle_end", _battle_end)
        self.subscribe("turn_start", _turn_start)
        self.subscribe("hit_landed", _hit_landed)
