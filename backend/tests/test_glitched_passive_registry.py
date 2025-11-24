"""Registry smoke tests for glitched-tier passive plugins."""

from importlib import import_module
import inspect
from pathlib import Path

from autofighter.passives import PassiveRegistry

GLITCHED_PLUGIN_DIR = Path(__file__).resolve().parents[1] / "plugins" / "passives" / "glitched"


def _discover_glitched_passive_classes() -> list[type]:
    """Import every glitched passive module and return concrete plugin classes."""

    glitched_classes: list[type] = []

    for module_path in GLITCHED_PLUGIN_DIR.glob("*.py"):
        if module_path.name == "__init__.py":
            continue

        module = import_module(f"plugins.passives.glitched.{module_path.stem}")
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != module.__name__:
                continue
            if getattr(cls, "plugin_type", None) != "passive":
                continue
            plugin_id = getattr(cls, "id", "")
            if plugin_id.endswith("_glitched"):
                glitched_classes.append(cls)

    return glitched_classes


def test_all_glitched_passives_registered_and_instantiable() -> None:
    """Ensure every glitched passive is discoverable and instantiates cleanly."""

    registry = PassiveRegistry()._registry
    glitched_classes = _discover_glitched_passive_classes()

    # Sanity check: list remains in sync with plugin directory contents.
    assert glitched_classes, "No glitched passive classes discovered"

    for cls in glitched_classes:
        plugin_id = getattr(cls, "id", "")
        assert plugin_id, f"Class {cls.__name__} is missing an ID"
        assert plugin_id in registry, f"{plugin_id} missing from PassiveRegistry"

        instance = registry[plugin_id]()
        assert instance.plugin_type == "passive"


def test_mimic_glitched_passive_removed() -> None:
    """Guard against the retired mimic passive sneaking back in."""

    registry = PassiveRegistry()._registry
    assert "mimic_player_copy_glitched" not in registry
