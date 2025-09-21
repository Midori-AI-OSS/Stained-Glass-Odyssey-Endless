from pathlib import Path

import pytest

from pathlib import Path

import pytest

from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.effects.critical_boost import CriticalBoost
from plugins.plugin_loader import PluginLoader


@pytest.mark.asyncio
async def test_critical_boost_stacking():
    stats = Stats()
    boost = CriticalBoost()
    await boost.apply(stats)
    await boost.apply(stats)
    assert stats.crit_rate == pytest.approx(0.05 + 0.005 * 2)
    assert stats.crit_damage == pytest.approx(2.0 + 0.05 * 2)
    BUS.unsubscribe("damage_taken", boost._on_damage_taken)


@pytest.mark.asyncio
async def test_critical_boost_resets_on_hit():
    stats = Stats()
    boost = CriticalBoost()
    await boost.apply(stats)
    await boost.apply(stats)
    await stats.apply_damage(10)
    assert stats.crit_rate == pytest.approx(0.05)
    assert stats.crit_damage == pytest.approx(2.0)
    assert boost.stacks == 0


def test_critical_boost_plugin_discovery():
    loader = PluginLoader()
    root = Path(__file__).resolve().parents[1] / "plugins" / "effects"
    loader.discover(root)
    plugins = loader.get_plugins("effects")
    assert "critical_boost" in plugins
