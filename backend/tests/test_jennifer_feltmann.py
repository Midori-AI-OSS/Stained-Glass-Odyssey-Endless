import importlib

import pytest

from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.characters.jennifer_feltmann import JenniferFeltmann
from plugins.damage_types.dark import Dark
from plugins.passives.glitched.bad_student import BadStudentGlitched
from plugins.passives.normal.bad_student import BadStudent
from plugins.passives.prime.bad_student import BadStudentPrime


def _build_attacker(effect_hit: float = 2.0) -> Stats:
    attacker = Stats(hp=1000, damage_type=Dark())
    attacker.effect_hit_rate = effect_hit
    return attacker


def _build_target(actions: float = 2.0, resistance: float = 0.0) -> Stats:
    target = Stats(hp=1000, damage_type=Dark())
    target.actions_per_turn = actions
    target.effect_resistance = resistance
    return target


@pytest.mark.asyncio
async def test_bad_student_applies_and_expires(monkeypatch) -> None:
    passive = BadStudent()
    attacker = _build_attacker(effect_hit=2.5)
    target = _build_target(actions=2.0)

    monkeypatch.setattr(
        "plugins.passives.normal.bad_student.random.random",
        lambda: 0.0,
    )

    try:
        await passive.apply(attacker, event="hit_landed", hit_target=target, action_type="attack")
        assert target.actions_per_turn == pytest.approx(1.25)

        # Two turns should keep the stack active
        await BUS.emit_async("turn_start", target)
        assert target.actions_per_turn == pytest.approx(1.25)
        await BUS.emit_async("turn_start", target)
        assert target.actions_per_turn == pytest.approx(1.25)

        # Third turn fully restores the action economy
        await BUS.emit_async("turn_start", target)
        assert target.actions_per_turn == pytest.approx(2.0)
    finally:
        await BadStudent._reset_state()


@pytest.mark.asyncio
async def test_bad_student_ultimate_chance_overrides(monkeypatch) -> None:
    passive = BadStudent()
    attacker = _build_attacker(effect_hit=1.0)
    target = _build_target(actions=2.0)

    # Use a roll that should fail for normal attacks but succeed for ultimates
    monkeypatch.setattr(
        "plugins.passives.normal.bad_student.random.random",
        lambda: 0.5,
    )

    try:
        await passive.apply(attacker, event="hit_landed", hit_target=target, action_type="attack")
        assert target.actions_per_turn == pytest.approx(2.0)

        await passive.apply(
            attacker,
            event="hit_landed",
            hit_target=target,
            action_type="generic_ultimate",
        )
        assert target.actions_per_turn == pytest.approx(1.25)
    finally:
        await BadStudent._reset_state()


@pytest.mark.asyncio
async def test_bad_student_prime_and_glitched_scaling(monkeypatch) -> None:
    monkeypatch.setattr(
        "plugins.passives.normal.bad_student.random.random",
        lambda: 0.0,
    )

    prime = BadStudentPrime()
    glitched = BadStudentGlitched()
    attacker = _build_attacker(effect_hit=3.0)

    prime_target = _build_target(actions=3.0)
    glitched_target = _build_target(actions=1.0)

    try:
        await prime.apply(attacker, event="hit_landed", hit_target=prime_target, action_type="attack")
        assert prime_target.actions_per_turn == pytest.approx(1.5)

        await glitched.apply(
            attacker,
            event="hit_landed",
            hit_target=glitched_target,
            action_type="generic_ultimate",
        )
        assert glitched_target.actions_per_turn == pytest.approx(0.1)
    finally:
        await BadStudentPrime._reset_state()
        await BadStudentGlitched._reset_state()


def test_jennifer_character_profile() -> None:
    jennifer = JenniferFeltmann()

    assert jennifer.char_type.name == "B"
    assert isinstance(jennifer.damage_type, Dark)
    assert jennifer.gacha_rarity == 5
    assert jennifer.voice_gender == "female_midrange"
    assert jennifer.passives == ["bad_student"]
    assert jennifer.hp == jennifer.max_hp == 1350
    assert jennifer.effect_hit_rate == pytest.approx(2.2)


def test_jennifer_in_gacha_pool() -> None:
    # Ensure module lists are refreshed in case of import ordering during the test suite
    gacha = importlib.import_module("autofighter.gacha")
    importlib.reload(gacha)

    assert "jennifer_feltmann" in gacha.FIVE_STAR
