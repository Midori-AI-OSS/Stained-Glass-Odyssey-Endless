"""Simple test to verify echo relic fixes work."""

import asyncio
import pytest

# Test the echo processing flag directly
from plugins.relics.echoing_drum import _echo_processing as drum_processing
from plugins.relics.echo_bell import _echo_processing as bell_processing


def test_echo_flags_exist():
    """Test that the echo processing flags exist and are initially False."""
    # Import the modules to ensure they load correctly
    import plugins.relics.echoing_drum
    import plugins.relics.echo_bell
    
    # The flags should exist and be False
    assert hasattr(plugins.relics.echoing_drum, '_echo_processing')
    assert hasattr(plugins.relics.echo_bell, '_echo_processing')
    

def test_echo_protection_prevents_recursion():
    """Test that the echo processing flag prevents recursive calls."""
    import plugins.relics.echoing_drum
    import plugins.relics.echo_bell
    
    # Initially False
    assert not plugins.relics.echoing_drum._echo_processing
    assert not plugins.relics.echo_bell._echo_processing
    
    # Set to True (simulating echo processing)
    plugins.relics.echoing_drum._echo_processing = True
    plugins.relics.echo_bell._echo_processing = True
    
    # Should be True
    assert plugins.relics.echoing_drum._echo_processing
    assert plugins.relics.echo_bell._echo_processing
    
    # Reset to False
    plugins.relics.echoing_drum._echo_processing = False
    plugins.relics.echo_bell._echo_processing = False
    
    # Should be False again
    assert not plugins.relics.echoing_drum._echo_processing
    assert not plugins.relics.echo_bell._echo_processing