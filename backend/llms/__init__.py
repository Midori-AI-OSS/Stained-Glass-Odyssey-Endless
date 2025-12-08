"""LLM and agent loading utilities."""

# New agent framework interface (recommended)
from .agent_loader import load_agent
from .agent_loader import validate_agent

# Legacy LLM loader interface (deprecated, use agent_loader instead)
from .loader import ModelName
from .loader import SupportsStream
from .loader import load_llm
from .loader import validate_lrm

# Keep existing utilities
from .torch_checker import is_torch_available
from .torch_checker import require_torch

__all__ = [
    # New agent framework interface (recommended)
    "load_agent",
    "validate_agent",
    # Legacy interface (deprecated)
    "load_llm",
    "validate_lrm",
    "ModelName",
    "SupportsStream",
    # Utilities
    "is_torch_available",
    "require_torch",
]
