import asyncio
from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))
import llms.torch_checker as torch_checker

from autofighter.party import Party
from autofighter.stats import BUS
from autofighter.stats import set_battle_active
from plugins.cards.supercell_conductor import SupercellConductor
from plugins.characters.ally import Ally
from plugins.characters.becca import Becca
from plugins.characters.foe_base import FoeBase
from plugins.characters.lady_storm import LadyStorm
from plugins.damage_types import load_damage_type


@pytest.mark.asyncio
async def test_supercell_conductor_bonus_action_and_debuff(monkeypatch):
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)
    card = SupercellConductor()
    storm = LadyStorm()
    storm.id = "storm"
    storm.spd = 400
    storm.atk = 200
    storm.effect_hit_rate = 1.0
    storm.damage_type = load_damage_type("Lightning")

    partner = Ally()
    partner.id = "partner"
    partner.spd = 220
    partner.damage_type = load_damage_type("Fire")

    party = Party(members=[storm, partner])
    await card.apply(party)

    foe = FoeBase()
    foe.id = "foe"
    foe.mitigation = 1.0

    extra_turns: list[object] = []

    def _record_extra_turn(actor):
        extra_turns.append(actor)

    BUS.subscribe("extra_turn", _record_extra_turn)
    set_battle_active(True)
    try:
        await BUS.emit_async("battle_start", storm)
        await BUS.emit_async("battle_start", partner)
        await BUS.emit_async("battle_start", foe)
        await asyncio.sleep(0)

        assert extra_turns and extra_turns[0] is storm

        base_atk = storm.atk
        base_effect_hit = storm.effect_hit_rate

        await BUS.emit_async("turn_start", storm)
        await BUS.emit_async("action_used", storm, foe, 0)
        assert storm.atk == pytest.approx(base_atk)
        assert storm.effect_hit_rate == pytest.approx(base_effect_hit)

        await BUS.emit_async("turn_start", storm)
        assert storm.atk == pytest.approx(base_atk * 0.5)
        assert storm.effect_hit_rate == pytest.approx(base_effect_hit * 1.3)

        await BUS.emit_async("hit_landed", storm, foe, 60, "attack", "tailwind_strike")
        await BUS.emit_async("action_used", storm, foe, 60)
        await asyncio.sleep(0)

        assert storm.atk == pytest.approx(base_atk)
        assert storm.effect_hit_rate == pytest.approx(base_effect_hit)
        assert foe.mitigation == pytest.approx(0.9)
    finally:
        BUS.unsubscribe("extra_turn", _record_extra_turn)
        await BUS.emit_async("battle_end", storm)
        await BUS.emit_async("battle_end", partner)
        await BUS.emit_async("battle_end", foe)
        set_battle_active(False)


@pytest.mark.asyncio
async def test_supercell_conductor_triggers_every_third_round(monkeypatch):
    monkeypatch.setattr(torch_checker, "is_torch_available", lambda: False)
    card = SupercellConductor()

    storm = LadyStorm()
    storm.id = "storm"
    storm.spd = 380
    storm.damage_type = load_damage_type("Wind")

    partner = Becca()
    partner.id = "becca"
    partner.spd = 200
    partner.damage_type = load_damage_type("Fire")

    party = Party(members=[storm, partner])
    await card.apply(party)

    foe = FoeBase()
    foe.id = "foe"

    extra_turns: list[str | None] = []

    def _record_extra_turn(actor):
        extra_turns.append(getattr(actor, "id", None))

    BUS.subscribe("extra_turn", _record_extra_turn)
    set_battle_active(True)
    try:
        await BUS.emit_async("battle_start", storm)
        await BUS.emit_async("battle_start", partner)
        await BUS.emit_async("battle_start", foe)
        await asyncio.sleep(0)
        assert extra_turns == ["storm"]

        async def resolve_tailwind_turn() -> None:
            await BUS.emit_async("turn_start", storm)
            await BUS.emit_async("action_used", storm, foe, 0)
            await BUS.emit_async("turn_start", storm)
            await BUS.emit_async("action_used", storm, foe, 0)
            await asyncio.sleep(0)

        async def resolve_normal_turn(actor) -> None:
            await BUS.emit_async("turn_start", actor)
            await BUS.emit_async("action_used", actor, foe, 0)
            await asyncio.sleep(0)

        await resolve_tailwind_turn()
        await resolve_normal_turn(partner)

        await resolve_normal_turn(storm)
        await resolve_normal_turn(partner)

        await resolve_normal_turn(storm)
        await resolve_normal_turn(partner)

        await BUS.emit_async("turn_start", storm)
        await asyncio.sleep(0)
        assert extra_turns.count("storm") == 2

        await BUS.emit_async("action_used", storm, foe, 0)
        await BUS.emit_async("turn_start", storm)
        await BUS.emit_async("action_used", storm, foe, 0)
        await resolve_normal_turn(partner)
    finally:
        BUS.unsubscribe("extra_turn", _record_extra_turn)
        await BUS.emit_async("battle_end", storm)
        await BUS.emit_async("battle_end", partner)
        await BUS.emit_async("battle_end", foe)
        set_battle_active(False)
