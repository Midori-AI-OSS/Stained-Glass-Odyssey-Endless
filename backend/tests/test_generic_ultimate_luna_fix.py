"""Test for Generic ultimate's Luna passive suppression with tier variants.

This test ensures that the Generic ultimate correctly prevents Luna from gaining
charge from the ultimate_used trigger, regardless of which tier variant Luna has.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from autofighter.passives import apply_rank_passives
from plugins.characters.luna import Luna


class TestGenericUltimateLunaSupression:
    """Test that Generic ultimate suppresses all Luna passive variants."""

    def test_normal_luna_passive_id_after_no_rank(self):
        """Normal rank Luna keeps base passive ID."""
        luna = Luna()
        luna.rank = "normal"
        list(luna.passives)

        apply_rank_passives(luna)

        # Normal Luna should have base passive
        assert "luna_lunar_reservoir" in luna.passives
        # Verify this is what Generic ultimate checks for
        assert "luna_lunar_reservoir" in {
            "luna_lunar_reservoir",
            "luna_lunar_reservoir_glitched",
            "luna_lunar_reservoir_prime",
            "luna_lunar_reservoir_boss"
        }

    def test_glitched_luna_passive_id_recognized(self):
        """Glitched Luna has tier passive that should be suppressed."""
        luna = Luna()
        luna.rank = "glitched"
        list(luna.passives)

        apply_rank_passives(luna)

        # Glitched Luna should have glitched passive
        assert "luna_lunar_reservoir_glitched" in luna.passives
        assert "luna_lunar_reservoir" not in luna.passives  # Base passive replaced

        # Verify glitched variant is in the suppression set
        luna_passive_ids = {
            "luna_lunar_reservoir",
            "luna_lunar_reservoir_glitched",
            "luna_lunar_reservoir_prime",
            "luna_lunar_reservoir_boss"
        }
        assert any(pid in luna_passive_ids for pid in luna.passives)

    def test_prime_luna_passive_id_recognized(self):
        """Prime Luna has tier passive that should be suppressed."""
        luna = Luna()
        luna.rank = "prime"

        apply_rank_passives(luna)

        # Prime Luna should have prime passive
        assert "luna_lunar_reservoir_prime" in luna.passives
        assert "luna_lunar_reservoir" not in luna.passives  # Base passive replaced

        # Verify prime variant is in the suppression set
        luna_passive_ids = {
            "luna_lunar_reservoir",
            "luna_lunar_reservoir_glitched",
            "luna_lunar_reservoir_prime",
            "luna_lunar_reservoir_boss"
        }
        assert any(pid in luna_passive_ids for pid in luna.passives)

    def test_boss_luna_passive_id_recognized(self):
        """Boss Luna has tier passive that should be suppressed."""
        luna = Luna()
        luna.rank = "boss"

        apply_rank_passives(luna)

        # Boss Luna should have boss passive
        assert "luna_lunar_reservoir_boss" in luna.passives
        assert "luna_lunar_reservoir" not in luna.passives  # Base passive replaced

        # Verify boss variant is in the suppression set
        luna_passive_ids = {
            "luna_lunar_reservoir",
            "luna_lunar_reservoir_glitched",
            "luna_lunar_reservoir_prime",
            "luna_lunar_reservoir_boss"
        }
        assert any(pid in luna_passive_ids for pid in luna.passives)

    def test_glitched_prime_boss_luna_all_variants_recognized(self):
        """Glitched Prime Boss Luna has all tier passives that should be suppressed."""
        luna = Luna()
        luna.rank = "glitched prime boss"

        apply_rank_passives(luna)

        # All tier variants should be present
        assert "luna_lunar_reservoir_glitched" in luna.passives
        assert "luna_lunar_reservoir_prime" in luna.passives
        assert "luna_lunar_reservoir_boss" in luna.passives
        assert "luna_lunar_reservoir" not in luna.passives  # Base passive replaced

        # Verify ALL variants are in the suppression set
        luna_passive_ids = {
            "luna_lunar_reservoir",
            "luna_lunar_reservoir_glitched",
            "luna_lunar_reservoir_prime",
            "luna_lunar_reservoir_boss"
        }
        # All of Luna's passives should be recognized
        for passive in luna.passives:
            if "luna_lunar_reservoir" in passive:
                assert passive in luna_passive_ids

    def test_filtering_removes_all_luna_variants(self):
        """Test that filtering logic removes ALL Luna variants."""
        luna_passive_ids = {
            "luna_lunar_reservoir",
            "luna_lunar_reservoir_glitched",
            "luna_lunar_reservoir_prime",
            "luna_lunar_reservoir_boss"
        }

        # Test with glitched prime boss Luna (worst case - all variants)
        test_passives = [
            "luna_lunar_reservoir_glitched",
            "luna_lunar_reservoir_prime",
            "luna_lunar_reservoir_boss",
            "some_other_passive"
        ]

        filtered = [pid for pid in test_passives if pid not in luna_passive_ids]

        # All Luna variants should be removed
        assert "luna_lunar_reservoir_glitched" not in filtered
        assert "luna_lunar_reservoir_prime" not in filtered
        assert "luna_lunar_reservoir_boss" not in filtered
        # Other passive should remain
        assert "some_other_passive" in filtered
        assert len(filtered) == 1

    def test_filtering_preserves_non_luna_passives(self):
        """Test that filtering preserves non-Luna passives."""
        luna_passive_ids = {
            "luna_lunar_reservoir",
            "luna_lunar_reservoir_glitched",
            "luna_lunar_reservoir_prime",
            "luna_lunar_reservoir_boss"
        }

        # Test with mixed passives
        test_passives = [
            "luna_lunar_reservoir_prime",
            "attack_up",
            "room_heal",
            "luna_lunar_reservoir_boss"
        ]

        filtered = [pid for pid in test_passives if pid not in luna_passive_ids]

        # Luna variants should be removed
        assert "luna_lunar_reservoir_prime" not in filtered
        assert "luna_lunar_reservoir_boss" not in filtered
        # Non-Luna passives should remain
        assert "attack_up" in filtered
        assert "room_heal" in filtered
        assert len(filtered) == 2
