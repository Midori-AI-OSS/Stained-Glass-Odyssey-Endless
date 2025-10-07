from __future__ import annotations

from collections.abc import Sequence
import random
from typing import Any


def select_aggro_target(
    enemies: Sequence[Any],
    *,
    rng: random.Random | None = None,
) -> tuple[int, Any]:
    """Return a living enemy selected using aggro weights.

    Parameters
    ----------
    enemies:
        Iterable of potential targets. Each item is inspected for an ``hp``
        attribute to determine whether it is alive and an ``aggro`` attribute to
        derive weighting. Objects missing either attribute fall back to sensible
        defaults (``hp`` > 0 and ``aggro`` = 0).
    rng:
        Optional :class:`random.Random` instance used for deterministic sampling
        (mostly in tests). When omitted, the module level :mod:`random` module is
        used.

    Returns
    -------
    tuple[int, Any]
        A pair of ``(index, target)`` referencing the original ``enemies``
        sequence.

    Raises
    ------
    ValueError
        If no living enemies are available in ``enemies``.
    """

    living_indices: list[int] = []
    living_targets: list[Any] = []
    weights: list[float] = []

    for index, foe in enumerate(enemies):
        try:
            hp = getattr(foe, "hp", 0)
        except Exception:
            hp = 0
        if hp <= 0:
            continue
        living_indices.append(index)
        living_targets.append(foe)
        try:
            weight = float(getattr(foe, "aggro", 0.0))
        except Exception:
            weight = 0.0
        weights.append(max(weight, 0.0))

    if not living_targets:
        raise ValueError("No living enemies available")

    rng = rng or random
    total_weight = sum(weights)

    if total_weight > 0:
        selection = rng.choices(range(len(living_targets)), weights=weights, k=1)[0]
    else:
        selection = rng.randrange(len(living_targets))

    return living_indices[selection], living_targets[selection]
