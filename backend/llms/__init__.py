"""LLM and agent loading utilities - NEW AGENT FRAMEWORK ONLY."""

# New agent framework interface (ONLY interface now)
from .agent_loader import get_agent_config
from .agent_loader import load_agent
from .agent_loader import validate_agent

# Keep existing utilities
from .torch_checker import is_torch_available
from .torch_checker import require_torch

__all__ = [
    # New interface (breaking change - old code must update)
    "load_agent",
    "validate_agent",
    "get_agent_config",
    # Utilities
    "is_torch_available",
    "require_torch",
]

# OLD INTERFACES REMOVED:
# - load_llm() - REMOVED, use load_agent() instead
# - SupportsStream - REMOVED, use MidoriAiAgentProtocol instead
# - ModelName - REMOVED, use string literals instead
# - validate_lrm() - REMOVED, use validate_agent() instead
