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

# Import route handlers (registers routes with blueprint)
# These imports register routes with the blueprint
from . import catalog  # noqa: F401
from . import editor  # noqa: F401
from . import materials  # noqa: F401
from . import stats  # noqa: F401
from . import upgrade_utils  # noqa: F401
from . import upgrades  # noqa: F401

# Export blueprint for app registration
__all__ = ["bp"]
