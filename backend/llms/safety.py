import os

from .torch_checker import is_torch_available

# Import torch only if available
if is_torch_available():
    import torch
else:
    torch = None

try:
    import psutil
except Exception:  # pragma: no cover - optional dependency
    psutil = None

try:
    from huggingface_hub import HfApi
except Exception:  # pragma: no cover - optional dependency
    HfApi = None


def get_available_memory() -> int:
    """Return available system memory in bytes."""
    if psutil is not None:
        return int(psutil.virtual_memory().available)
    if hasattr(os, "sysconf"):
        page_size = os.sysconf("SC_PAGE_SIZE")
        avail_pages = os.sysconf("SC_AVPHYS_PAGES")
        return int(page_size * avail_pages)
    return 0


def get_available_vram() -> int | None:
    """Return total VRAM for CUDA device 0 in bytes, if available."""
    if torch is not None and torch.cuda.is_available():
        return int(torch.cuda.get_device_properties(0).total_memory)
    return None


def ensure_ram(required: int) -> None:
    """Raise RuntimeError when available RAM is below ``required`` bytes."""
    available = get_available_memory()
    if available < required:
        msg = (
            f"{required / 2**30:.1f}GB system memory required, "
            f"but only {available / 2**30:.1f}GB detected"
        )
        raise RuntimeError(msg)


def pick_device(min_vram: int | None = None) -> int:
    """Return 0 for GPU if ``min_vram`` satisfied, else -1 for CPU."""
    available_vram = get_available_vram()
    if available_vram is not None and (min_vram is None or available_vram >= min_vram):
        return 0
    if min_vram is not None:
        msg = (
            f"{min_vram / 2**30:.1f}GB VRAM required, "
            f"but only {(available_vram or 0) / 2**30:.1f}GB detected"
        )
        raise RuntimeError(msg)
    return -1


def model_memory_requirements(model: str) -> tuple[int, int]:
    """Estimate RAM and VRAM requirements in bytes for a Hugging Face model."""
    if HfApi is None:
        return 0, 0
    api = HfApi()
    try:  # pragma: no cover - network dependent
        info = api.model_info(model, files_metadata=True)
    except Exception:  # pragma: no cover - network dependent
        return 0, 0
    size = 0
    for file in info.siblings:
        if file.rfilename.endswith((".safetensors", ".bin")) and file.size is not None:
            size += file.size
    if size == 0:
        return 0, 0
    return int(size * 2), int(size)


__all__ = [
    "ensure_ram",
    "get_available_memory",
    "get_available_vram",
    "model_memory_requirements",
    "pick_device",
]
