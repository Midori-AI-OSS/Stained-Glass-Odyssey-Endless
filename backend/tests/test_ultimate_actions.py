import pytest

from autofighter.stats import BUS, Stats
from plugins.actions.registry import ActionRegistry
from plugins.actions.ultimate.dark_ultimate import DarkUltimate
from plugins.actions.ultimate.fire_ultimate import FireUltimate
from plugins.actions.ultimate.generic_ultimate import GenericUltimate
from plugins.actions.ultimate.ice_ultimate import IceUltimate
from plugins.actions.ultimate.light_ultimate import LightUltimate
from plugins.actions.ultimate.lightning_ultimate import LightningUltimate
from plugins.actions.ultimate.utils import run_ultimate_action
from plugins.actions.ultimate.wind_ultimate import WindUltimate
from plugins.damage_types.dark import Dark
from plugins.damage_types.fire import Fire
from plugins.damage_types.generic import Generic
from plugins.damage_types.ice import Ice
from plugins.damage_types.light import Light
from plugins.damage_types.lightning import Lightning
from plugins.damage_types.wind import Wind


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


@pytest.mark.asyncio
async def test_ultimate_dark() -> None:
    registry = ActionRegistry()
    registry.register_action(DarkUltimate)

    action = registry.instantiate_ultimate("Dark")
    assert isinstance(action, DarkUltimate)

    actor = DummyCombatant(damage_type=Dark())
    enemy = Stats()
    actor.add_ultimate_charge(actor.ultimate_charge_max)

    result = await run_ultimate_action(
        DarkUltimate,
        actor,
        [actor],
        [enemy],
    )

    assert result.success is True
    assert result.damage_dealt
    assert result.metadata["damage"] == actor.atk
    assert result.metadata["stacks"] == 0


@pytest.mark.asyncio
async def test_ultimate_wind() -> None:
    registry = ActionRegistry()
    registry.register_action(WindUltimate)

    action = registry.instantiate_ultimate("Wind")
    assert isinstance(action, WindUltimate)

    actor = DummyCombatant(damage_type=Wind())
    enemy = Stats()
    actor.add_ultimate_charge(actor.ultimate_charge_max)

    result = await run_ultimate_action(
        WindUltimate,
        actor,
        [actor],
        [enemy],
    )

    assert result.success is True
    assert result.damage_dealt
    assert result.metadata["damage_type"] == "Wind"
    assert result.metadata["hits"] > 0


@pytest.mark.asyncio
async def test_ultimate_fire() -> None:
    registry = ActionRegistry()
    registry.register_action(FireUltimate)

    action = registry.instantiate_ultimate("Fire")
    assert isinstance(action, FireUltimate)

    actor = DummyCombatant(damage_type=Fire())
    enemy = Stats()
    actor.add_ultimate_charge(actor.ultimate_charge_max)

    result = await run_ultimate_action(
        FireUltimate,
        actor,
        [actor],
        [enemy],
    )

    assert result.success is True
    assert result.damage_dealt
    assert result.metadata["hits"] == 1
    assert result.metadata["damage"] == actor.atk


@pytest.mark.asyncio
async def test_ultimate_ice() -> None:
    registry = ActionRegistry()
    registry.register_action(IceUltimate)

    action = registry.instantiate_ultimate("Ice")
    assert isinstance(action, IceUltimate)

    actor = DummyCombatant(damage_type=Ice())
    enemy = Stats()
    actor.add_ultimate_charge(actor.ultimate_charge_max)

    result = await run_ultimate_action(
        IceUltimate,
        actor,
        [actor],
        [enemy],
    )

    assert result.success is True
    assert result.damage_dealt
    assert result.metadata["damage"] == actor.atk
    assert result.metadata["hits"] > 0


@pytest.mark.asyncio
async def test_ultimate_lightning() -> None:
    registry = ActionRegistry()
    registry.register_action(LightningUltimate)

    action = registry.instantiate_ultimate("Lightning")
    assert isinstance(action, LightningUltimate)

    actor = DummyCombatant(damage_type=Lightning())
    enemy = Stats()
    actor.add_ultimate_charge(actor.ultimate_charge_max)

    result = await run_ultimate_action(
        LightningUltimate,
        actor,
        [actor],
        [enemy],
    )

    assert result.success is True
    assert result.damage_dealt
    assert result.metadata["hits"] == 1
    assert result.metadata["stacks"] == getattr(actor, "_lightning_aftertaste_stacks")


@pytest.mark.asyncio
async def test_ultimate_generic() -> None:
    registry = ActionRegistry()
    registry.register_action(GenericUltimate)

    action = registry.instantiate_ultimate("Generic")
    assert isinstance(action, GenericUltimate)

    actor = DummyCombatant(damage_type=Generic())
    enemy = Stats()
    actor.add_ultimate_charge(actor.ultimate_charge_max)

    result = await run_ultimate_action(
        GenericUltimate,
        actor,
        [actor],
        [enemy],
    )

    assert result.success is True
    assert result.damage_dealt
    assert result.metadata["damage"] == actor.atk
    assert result.metadata["hits"] > 0
