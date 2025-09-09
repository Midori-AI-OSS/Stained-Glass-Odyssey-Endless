__all__ = ["EventBus", "PluginLoader"]


def __getattr__(name: str):
    if name == "EventBus":
        from plugins.event_bus import EventBus

        return EventBus
    if name == "PluginLoader":
        from plugins.plugin_loader import PluginLoader

        return PluginLoader
    raise AttributeError(name)
