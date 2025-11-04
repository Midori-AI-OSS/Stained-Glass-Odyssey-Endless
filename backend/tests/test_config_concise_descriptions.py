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
    

def test_catalog_sends_both_description_fields():
    """Test that catalog routes send both full_about and summarized_about fields."""
    catalog_file = Path(__file__).resolve().parents[1] / "routes" / "catalog.py"
    content = catalog_file.read_text()
    
    # Backend should send BOTH fields, not choose one based on settings
    assert "full_about" in content
    assert "summarized_about" in content
    assert '"full_about": full_about_text' in content
    assert '"summarized_about": summarized_about_text' in content


def test_players_route_sends_both_description_fields():
    """Test that players routes send both full_about and summarized_about fields."""
    players_file = Path(__file__).resolve().parents[1] / "routes" / "players.py"
    content = players_file.read_text()
    
    # Backend should send BOTH fields, not choose one based on settings
    assert "full_about" in content
    assert "summarized_about" in content
    assert '"full_about": full_about_text' in content
    assert '"summarized_about": summarized_about_text' in content
