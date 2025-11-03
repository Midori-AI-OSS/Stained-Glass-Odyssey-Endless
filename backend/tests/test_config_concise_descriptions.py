import importlib.util
from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))


def test_concise_descriptions_backend_imports():
    """Test that backend routes properly import the concise_descriptions option."""
    config_file = Path(__file__).resolve().parents[1] / "routes" / "config.py"
    content = config_file.read_text()
    
    assert "OptionKey.CONCISE_DESCRIPTIONS" in content
    assert "@bp.get(\"/concise_descriptions\")" in content
    assert "@bp.post(\"/concise_descriptions\")" in content
    

def test_catalog_uses_concise_descriptions():
    """Test that catalog routes check the concise_descriptions setting."""
    catalog_file = Path(__file__).resolve().parents[1] / "routes" / "catalog.py"
    content = catalog_file.read_text()
    
    assert "concise = get_option(OptionKey.CONCISE_DESCRIPTIONS" in content
    assert "summarized_about" in content
    assert "full_about" in content


def test_players_route_uses_concise_descriptions():
    """Test that players routes check the concise_descriptions setting."""
    players_file = Path(__file__).resolve().parents[1] / "routes" / "players.py"
    content = players_file.read_text()
    
    assert "concise = get_option(OptionKey.CONCISE_DESCRIPTIONS" in content
    assert "summarized_about" in content
    assert "full_about" in content
