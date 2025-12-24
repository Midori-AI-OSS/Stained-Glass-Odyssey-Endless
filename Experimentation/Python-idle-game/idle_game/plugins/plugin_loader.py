"""Plugin loader for idle game - simplified version of backend's plugin loader."""
from __future__ import annotations

import importlib.util
import logging
from pathlib import Path
import sys
from types import ModuleType

log = logging.getLogger(__name__)


class PluginLoader:
    """Loads and registers plugins from a directory."""

    def __init__(self) -> None:
        self._registry: dict[str, dict[str, type]] = {}

    def discover(self, root: str) -> None:
        """Discover and load all plugins in the root directory."""
        base = Path(root)
        if not base.exists():
            log.warning(f"Plugin directory does not exist: {root}")
            return

        failures: list[tuple[Path, Exception]] = []
        for path in base.rglob("*.py"):
            if path.name == "__init__.py" or path.name.startswith("_"):
                continue
            try:
                module = self._import_module(path)
            except Exception as exc:
                log.exception("Failed to import plugin %s", path)
                failures.append((path, exc))
                continue
            self._register_module(module)

        if failures:
            details = ", ".join(
                f"{path} ({type(err).__name__}: {err})" for path, err in failures
            )
            log.warning(f"Failed to import plugin(s): {details}")

        for category, plugins in self._registry.items():
            log.info("Loaded %d %s plugin(s)", len(plugins), category)

    def get_plugins(self, category: str) -> dict[str, type]:
        """Get all plugins for a given category."""
        if category not in self._registry:
            return {}
        return self._registry[category]

    def _import_module(self, path: Path) -> ModuleType:
        """Import a module from a file path."""
        parts = path.with_suffix("").parts
        try:
            idx = parts.index("plugins")
            module_name = ".".join(parts[idx:])
        except ValueError:
            module_name = path.stem

        spec = importlib.util.spec_from_file_location(module_name, path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        parent = module_name.rpartition(".")[0]
        if parent:
            pkg_path = path.parent
            pkg_name = parent
            parents: list[tuple[str, Path]] = []
            while pkg_name and pkg_name not in sys.modules:
                parents.append((pkg_name, pkg_path))
                pkg_name, pkg_path = pkg_name.rpartition(".")[0], pkg_path.parent
            for name, pth in reversed(parents):
                pkg = ModuleType(name)
                pkg.__path__ = [str(pth)]
                sys.modules[name] = pkg
            module.__package__ = parent
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    def _register_module(self, module: ModuleType) -> None:
        """Register all plugin classes in a module."""
        for obj in module.__dict__.values():
            if not isinstance(obj, type):
                continue
            if getattr(obj, "plugin_type", None) is None:
                continue
            if getattr(obj, "__module__", "") != module.__name__:
                continue
            category = obj.plugin_type
            plugin_id = getattr(obj, "id", obj.__name__)
            self._registry.setdefault(category, {})[plugin_id] = obj
