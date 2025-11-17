"""Action plugin infrastructure package.

The loader-facing modules live here so follow-up tasks can import
`ActionBase`, `ActionRegistry`, and the shared context/result helpers from a
single place.  This makes it trivial for the battle turn loop to rely on the
new plugin ecosystem without reaching into private modules.
"""

from ._base import ActionAnimationPlan
from ._base import ActionBase
from ._base import ActionCostBreakdown
from ._base import ActionType
from ._base import TargetingRules
from ._base import TargetScope
from ._base import TargetSide
from .context import BattleContext
from .registry import ActionRegistry
from .result import ActionResult

__all__ = [
    "ActionAnimationPlan",
    "ActionBase",
    "ActionCostBreakdown",
    "ActionRegistry",
    "ActionResult",
    "ActionType",
    "BattleContext",
    "TargetScope",
    "TargetSide",
    "TargetingRules",
]
