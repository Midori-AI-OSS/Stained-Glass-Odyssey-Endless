"""UI and game interaction routes.

This module provides API endpoints for:
- Game state management (state.py)
- UI action handling (actions.py)
- Battle information (battles.py)
- Run management (runs.py)
- Save management (saves.py)
- Utility functions (utils.py)
"""

from quart import Blueprint

# Create blueprint
bp = Blueprint("ui", __name__)

# Import route handlers after blueprint creation to avoid circular imports.
# Each handler module imports bp via 'from . import bp' to register routes,
# so bp must be created before importing the handler modules.
from . import actions  # noqa: F401
from . import battles  # noqa: F401
from . import runs  # noqa: F401
from . import saves  # noqa: F401
from . import state  # noqa: F401
from . import utils  # noqa: F401

# Export blueprint for app registration
__all__ = ["bp"]
