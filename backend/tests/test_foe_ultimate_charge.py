from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.damage_types.generic import Generic
from plugins.foes._base import FoeBase
from plugins.players._base import PlayerBase


def test_foe_ultimate_charge_consumption():
    """Test that foes can properly gain and consume ultimate charge."""
    # Use Stats with plugin_type to avoid import issues
    foe = Stats(damage_type=Generic())
    foe.plugin_type = "foe"

    # Manually add the use_ultimate method from FoeBase
    from plugins.foes._base import FoeBase

    foe.use_ultimate = FoeBase.use_ultimate.__get__(foe, Stats)

    # Initially no charge
    assert foe.ultimate_charge == 0
    assert foe.ultimate_ready is False

    # Add charge and verify it accumulates
    foe.add_ultimate_charge(10)
    assert foe.ultimate_charge == 10
    assert foe.ultimate_ready is False

    # Add more charge to reach maximum
    foe.add_ultimate_charge(5)
    assert foe.ultimate_charge == 15
    assert foe.ultimate_ready is True

    # Use ultimate and verify charge is consumed
    result = foe.use_ultimate()
    assert result is True
    assert foe.ultimate_charge == 0
    assert foe.ultimate_ready is False


def test_foe_ultimate_ready_behavior():
    """Test that foe ultimate behaves the same as player ultimate."""
    # Create foe and player using Stats
    foe = Stats(damage_type=Generic())
    foe.plugin_type = "foe"
    foe.use_ultimate = FoeBase.use_ultimate.__get__(foe, Stats)

    player = Stats(damage_type=Generic())
    player.plugin_type = "player"
    player.use_ultimate = PlayerBase.use_ultimate.__get__(player, Stats)

    # Both should start with no charge
    assert foe.ultimate_charge == player.ultimate_charge == 0
    assert foe.ultimate_ready == player.ultimate_ready is False

    # Add charge to both
    foe.add_ultimate_charge(15)
    player.add_ultimate_charge(15)

    assert foe.ultimate_ready == player.ultimate_ready is True
    assert foe.ultimate_charge == player.ultimate_charge == 15

    # Use ultimates for both
    foe_result = foe.use_ultimate()
    player_result = player.use_ultimate()

    assert foe_result == player_result is True
    assert foe.ultimate_charge == player.ultimate_charge == 0
    assert foe.ultimate_ready == player.ultimate_ready is False


def test_foe_ultimate_events():
    """Test that foe ultimate emits the correct events."""
    foe = Stats(damage_type=Generic())
    foe.plugin_type = "foe"
    foe.use_ultimate = FoeBase.use_ultimate.__get__(foe, Stats)
    foe.add_ultimate_charge(15)

    # Track events
    events = []

    def track_event(entity):
        events.append(entity)

    BUS.subscribe("ultimate_used", track_event)

    try:
        # Use ultimate and check event was emitted
        result = foe.use_ultimate()
        assert result is True
        assert len(events) == 1
        assert events[0] is foe
    finally:
        BUS.unsubscribe("ultimate_used", track_event)


def test_foe_cannot_use_ultimate_when_not_ready():
    """Test that foe cannot use ultimate when not ready."""
    foe = Stats(damage_type=Generic())
    foe.plugin_type = "foe"
    foe.use_ultimate = FoeBase.use_ultimate.__get__(foe, Stats)

    # Try to use ultimate without enough charge
    result = foe.use_ultimate()
    assert result is False
    assert foe.ultimate_charge == 0
    assert foe.ultimate_ready is False

    # Add partial charge and try again
    foe.add_ultimate_charge(10)
    result = foe.use_ultimate()
    assert result is False
    assert foe.ultimate_charge == 10  # Should not change
    assert foe.ultimate_ready is False
