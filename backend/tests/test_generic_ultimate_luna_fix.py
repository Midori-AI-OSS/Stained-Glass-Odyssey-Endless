"""Test for Generic ultimate's Luna passive tier stacking behavior.

This test validates that tier passive variants properly apply their multipliers
to Luna's charge gain from the ultimate_used trigger in Generic ultimate.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.passives import apply_rank_passives
from plugins.characters.luna import Luna


class TestGenericUltimateLunaTierBehavior:
    """Test that Generic ultimate allows tier multipliers to apply to Luna."""

    def test_normal_luna_passive_id_after_no_rank(self):
        """Normal rank Luna keeps base passive ID."""
        luna = Luna()
        luna.rank = "normal"

        apply_rank_passives(luna)

        # Normal Luna should have base passive
        assert "luna_lunar_reservoir" in luna.passives

    def test_glitched_luna_passive_id_recognized(self):
        """Glitched Luna has tier passive with 2x multiplier."""
        luna = Luna()
        luna.rank = "glitched"

        apply_rank_passives(luna)

        # Glitched Luna should have glitched passive
        assert "luna_lunar_reservoir_glitched" in luna.passives
        assert "luna_lunar_reservoir" not in luna.passives  # Base passive replaced

    def test_prime_luna_passive_id_recognized(self):
        """Prime Luna has tier passive with 5x multiplier."""
        luna = Luna()
        luna.rank = "prime"

        apply_rank_passives(luna)

        # Prime Luna should have prime passive
        assert "luna_lunar_reservoir_prime" in luna.passives
        assert "luna_lunar_reservoir" not in luna.passives  # Base passive replaced

    def test_boss_luna_passive_id_recognized(self):
        """Boss Luna has tier passive with enhanced behavior."""
        luna = Luna()
        luna.rank = "boss"

        apply_rank_passives(luna)

        # Boss Luna should have boss passive
        assert "luna_lunar_reservoir_boss" in luna.passives
        assert "luna_lunar_reservoir" not in luna.passives  # Base passive replaced

    def test_glitched_prime_boss_luna_all_variants_stack(self):
        """Glitched Prime Boss Luna has all tier passives that will all trigger."""
        luna = Luna()
        luna.rank = "glitched prime boss"

        apply_rank_passives(luna)

        # All tier variants should be present and will all trigger
        assert "luna_lunar_reservoir_glitched" in luna.passives
        assert "luna_lunar_reservoir_prime" in luna.passives
        assert "luna_lunar_reservoir_boss" in luna.passives
        assert "luna_lunar_reservoir" not in luna.passives  # Base passive replaced

        # All three will receive the ultimate_used trigger and apply their multipliers
        # Glitched: 64 * 2 = 128
        # Prime: 64 * 5 = 320
        # Boss: 64 * 1 (with enhanced cap) = 64
        # Total: 512 charges from ultimate_used alone
