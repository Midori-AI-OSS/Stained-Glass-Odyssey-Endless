"""Player management routes.

This module provides API endpoints for:
- Player catalog and listing (catalog.py)
- Player statistics (stats.py)
- Player customization (editor.py)
- Material crafting and parsing (materials.py)
- Star system upgrades (upgrades.py)
- Upgrade utilities (upgrade_utils.py)
"""

from quart import Blueprint

# Create blueprint
bp = Blueprint("players", __name__)

# Import route handlers after blueprint creation to avoid circular imports.
# Each handler module imports bp via 'from . import bp' to register routes,
# so bp must be created before importing the handler modules.
from . import catalog  # noqa: F401
from . import editor  # noqa: F401
from . import materials  # noqa: F401
from . import stats  # noqa: F401
from . import upgrade_utils  # noqa: F401
from . import upgrades  # noqa: F401

# Export blueprint for app registration
__all__ = ["bp"]
