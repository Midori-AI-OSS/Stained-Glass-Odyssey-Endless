from dataclasses import dataclass
import types
from typing import Callable

import pytest

from autofighter.rooms.foes.selector import _choose_template
from autofighter.rooms.foes.selector import _desired_count
from autofighter.rooms.foes.selector import _sample_templates
from autofighter.rooms.foes.selector import _weight_for_template


@dataclass(frozen=True)
class Template:
    id: str
    cls: type
    tags: frozenset[str] = frozenset()
    weight_hook: Callable[..., float] | None = None
    base_rank: str = "normal"
    apply_adjective: bool = False


class DummyFoe:
    plugin_type = "foe"


class DummyNode:
    def __init__(self, *, pressure: int = 0) -> None:
        self.pressure = pressure


class DummyParty:
    def __init__(self, members: list[types.SimpleNamespace]) -> None:
        self.members = members


class DeterministicRng:
    """Deterministic helper that prefers highest-weight options."""

    def __init__(self, values: list[float] | None = None) -> None:
        self._values = list(values or [])
        self._index = 0

    def random(self) -> float:
        if self._index < len(self._values):
            value = self._values[self._index]
            self._index += 1
            return value
        return 0.0

    def choices(self, population, weights=None, k=1):  # noqa: D401 - matches random API
        if weights and any(weight > 0 for weight in weights):
            max_weight = max(weights)
            index = weights.index(max_weight)
        else:
            index = 0
        return [population[index] for _ in range(k)]


def make_template(identifier: str, weight: float = 1.0, *, tags: frozenset[str] | None = None):
    calls: list[dict[str, object]] = []

    def hook(**kwargs):
        calls.append(kwargs)
        return weight

    template = Template(
        id=identifier,
        cls=DummyFoe,
        tags=tags or frozenset(),
        weight_hook=hook,
    )
    hook.calls = calls  # type: ignore[attr-defined]
    return template


def test_weight_for_template_defaults_without_hook():
    template = Template(id="plain", cls=DummyFoe)
    node = DummyNode()
    weight = _weight_for_template(
        template,
        node=node,
        party_ids=set(),
        recent_ids=None,
        boss=False,
    )
    assert weight == pytest.approx(1.0)


def test_sample_templates_prioritises_non_recent_ids():
    fresh = make_template("fresh", weight=1.0)
    recent = make_template("recent", weight=1.0)
    templates = {"fresh": fresh, "recent": recent}
    node = DummyNode()
    rng = DeterministicRng()

    selected = _sample_templates(
        1,
        templates=templates,
        node=node,
        party_ids=set(),
        recent_ids={"recent"},
        config={
            "recent_weight_factor": 0.25,
            "recent_weight_min": 0.1,
        },
        rng=rng,
    )

    assert [template.id for template in selected] == ["fresh"]
    assert fresh.weight_hook.calls[0]["boss"] is False


def test_sample_templates_ignores_party_members():
    ally = make_template("ally", weight=10.0)
    other = make_template("other", weight=1.0)
    templates = {"ally": ally, "other": other}
    node = DummyNode()
    rng = DeterministicRng()

    selected = _sample_templates(
        1,
        templates=templates,
        node=node,
        party_ids={"ally"},
        recent_ids=set(),
        config={},
        rng=rng,
    )

    assert [template.id for template in selected] == ["other"]


def test_sample_templates_falls_back_when_all_weights_zero():
    zero = make_template("zero", weight=0.0)
    templates = {"zero": zero}
    node = DummyNode()

    selected = _sample_templates(
        1,
        templates=templates,
        node=node,
        party_ids=set(),
        recent_ids=set(),
        config={},
        rng=DeterministicRng(),
    )

    assert [template.id for template in selected] == ["zero"]


def test_choose_template_passes_boss_flag():
    recorded: list[bool] = []

    def hook(**kwargs):
        recorded.append(bool(kwargs.get("boss")))
        return 5.0

    template = Template(
        id="bossy",
        cls=DummyFoe,
        weight_hook=hook,
    )
    result = _choose_template(
        templates={"bossy": template},
        node=DummyNode(),
        party_ids=set(),
        recent_ids=None,
        boss=True,
        rng=DeterministicRng(),
    )

    assert result is template
    assert recorded == [True]


def test_desired_count_uses_full_party_bonus():
    node = DummyNode(pressure=10)
    members = [types.SimpleNamespace(id=str(idx)) for idx in range(4)]
    party = DummyParty(members)
    rng = DeterministicRng([0.2])  # triggers full bonus

    result = _desired_count(
        node,
        party,
        config={
            "base_spawn_cap": 10,
            "pressure_spawn_base": 1,
            "pressure_spawn_step": 5,
            "party_extra_full_chance": 0.35,
            "party_extra_step_chance": 0.75,
        },
        rng=rng,
    )

    assert result == 6


def test_desired_count_partial_bonus_steps():
    node = DummyNode(pressure=5)
    members = [types.SimpleNamespace(id=str(idx)) for idx in range(5)]
    party = DummyParty(members)
    rng = DeterministicRng([0.9, 0.4])  # skip full bonus, apply tier bonus

    result = _desired_count(
        node,
        party,
        config={
            "base_spawn_cap": 10,
            "pressure_spawn_base": 1,
            "pressure_spawn_step": 5,
            "party_extra_full_chance": 0.35,
            "party_extra_step_chance": 0.75,
        },
        rng=rng,
    )

    assert result == 5
