import pytest

from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.actions.registry import ActionRegistry
from plugins.actions.ultimate.light_ultimate import LightUltimate
from plugins.actions.ultimate.utils import run_ultimate_action
from plugins.damage_types.light import Light


class DummyCombatant(Stats):
    async def use_ultimate(self) -> bool:  # pragma: no cover - simple helper
        if not getattr(self, "ultimate_ready", False):
            return False
        self.ultimate_charge = 0
        self.ultimate_ready = False
        await BUS.emit_async("ultimate_used", self)
        return True


def test_action_registry_tracks_ultimate_actions() -> None:
    registry = ActionRegistry()
    registry.register_action(LightUltimate)

    action = registry.instantiate_ultimate("Light")
    assert isinstance(action, LightUltimate)

    lower_action = registry.instantiate_ultimate("light")
    assert isinstance(lower_action, LightUltimate)
    assert lower_action.id == action.id


@pytest.mark.asyncio
async def test_run_ultimate_action_executes_plugin_logic() -> None:
    light = Light()
    actor = DummyCombatant(damage_type=light)
    ally = Stats()
    ally._base_max_hp = 100
    ally.hp = 10
    enemy = Stats()

    actor.add_ultimate_charge(actor.ultimate_charge_max)

    result = await run_ultimate_action(
        LightUltimate,
        actor,
        [actor, ally],
        [enemy],
    )

    assert result.success is True
    assert ally.hp == ally.max_hp
    assert actor.ultimate_ready is False
