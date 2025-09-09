"""Centralized torch availability checker.

This module performs a single check on import to determine if torch and
related dependencies are available. All LLM/LRM modules should use this
instead of attempting their own imports.
"""

import logging

log = logging.getLogger(__name__)

# Global flags set once on module import
_TORCH_AVAILABLE = False
_TORCH_IMPORT_ERROR = None

# Try to import torch and related dependencies once
try:
    from langchain_community.llms import llamacpp as LlamaCpp  # noqa: F401
    from langchain_huggingface import HuggingFacePipeline  # noqa: F401
    import torch  # noqa: F401
    from transformers import pipeline  # noqa: F401

    _TORCH_AVAILABLE = True
    log.info("Torch and LLM dependencies are available")
except Exception as err:
    _TORCH_AVAILABLE = False
    _TORCH_IMPORT_ERROR = err
    log.warning("Torch and LLM dependencies are not available: %s", err)


def is_torch_available() -> bool:
    """Check if torch and LLM dependencies are available.

    Returns:
        True if torch can be imported, False otherwise.
    """
    return _TORCH_AVAILABLE


def get_torch_import_error() -> Exception | None:
    """Get the import error that occurred when trying to load torch.

    Returns:
        The exception that occurred during import, or None if import succeeded.
    """
    return _TORCH_IMPORT_ERROR


def require_torch() -> None:
    """Raise an error if torch is not available.

    Raises:
        RuntimeError: If torch dependencies are not available.
    """
    if not _TORCH_AVAILABLE:
        msg = (
            "LLM dependencies are not installed. Install extras to enable LLM features."
        )
        raise RuntimeError(msg) from _TORCH_IMPORT_ERROR


__all__ = ["is_torch_available", "get_torch_import_error", "require_torch"]
