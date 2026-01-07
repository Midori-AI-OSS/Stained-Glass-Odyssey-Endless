"""Guidebook and reference information routes.

This module provides API endpoints for:
- Damage types and elemental information (reference.py)
- Ultimates, passives, effects, shops information (reference.py)
- Stats reference (stats_guide.py)
- Helper utilities (helpers.py)
"""

from quart import Blueprint

# Create blueprint
bp = Blueprint("guidebook", __name__)

# Import route handlers after blueprint creation to avoid circular imports.
# Each handler module imports bp via 'from . import bp' to register routes,
# so bp must be created before importing the handler modules.
from . import helpers  # noqa: F401
from . import reference  # noqa: F401
from . import stats_guide  # noqa: F401

# Export blueprint for app registration
__all__ = ["bp"]
