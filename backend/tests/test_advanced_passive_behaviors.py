import pytest

from autofighter.passives import PassiveRegistry
from autofighter.stats import Stats


class TestAdvancedPassiveBehaviors:
    """Test advanced passive behavior mechanics."""

    @pytest.fixture
    def registry(self):
        return PassiveRegistry()

    @pytest.fixture
    def party_member(self):
        member = Stats()
        member.id = "test_member"
        member.hp = 800
        member.passives = ["advanced_combat_synergy"]
        return member

    @pytest.fixture
    def party(self, party_member):
        ally1 = Stats()
        ally1.id = "ally1"
        ally1.hp = 900

        ally2 = Stats()
        ally2.id = "ally2"
        ally2.hp = 850

        return [party_member, ally1, ally2]

    @pytest.fixture
    def target_foe(self):
        foe = Stats()
        foe.id = "test_foe"
        foe.set_base_stat("max_hp", 1000)
        foe.hp = 400  # Below 50% of 1000 max HP
        return foe

    @pytest.mark.asyncio
    async def test_hit_landed_conditional_trigger(self, registry, party_member, party, target_foe):
        """Test that hit_landed passives trigger conditionally based on target HP."""

        # Test conditional trigger when target is below 50% HP
        await registry.trigger_hit_landed(
            party_member,
            target_foe,
            damage=100,
            action_type="attack",
            party=party
        )

        # Check that allies received the buff (excluding the acting member)
        for ally in party:
            if ally != party_member:
                effects = ally.get_active_effects()
                boost_effects = [e for e in effects if e.name == "advanced_combat_synergy_ally_atk_boost"]
                assert len(boost_effects) == 1
                assert boost_effects[0].stat_modifiers["atk"] == 10
                assert boost_effects[0].duration == 3

    @pytest.mark.asyncio
    async def test_hit_landed_no_trigger_above_threshold(self, registry, party_member, party):
        """Test that conditional trigger doesn't fire when target is above 50% HP."""

        healthy_foe = Stats()
        healthy_foe.id = "healthy_foe"
        healthy_foe.set_base_stat("max_hp", 1000)
        healthy_foe.hp = 800  # Above 50% of 1000 max HP

        await registry.trigger_hit_landed(
            party_member,
            healthy_foe,
            damage=100,
            action_type="attack",
            party=party
        )

        # Check that no allies received buffs since condition wasn't met
        for ally in party:
            if ally != party_member:
                effects = ally.get_active_effects()
                boost_effects = [e for e in effects if e.name == "advanced_combat_synergy_ally_atk_boost"]
                assert len(boost_effects) == 0

    @pytest.mark.asyncio
    async def test_turn_start_dynamic_behavior(self, registry, party_member, party):
        """Test turn_start trigger with dynamic behavior based on party state."""

        # First verify the passive was discovered
        assert "advanced_combat_synergy" in registry._registry

        # Create a member with turn_start trigger specifically
        turn_start_member = Stats()
        turn_start_member.id = "turn_start_member"
        turn_start_member.passives = ["advanced_combat_synergy"]

        await registry.trigger_turn_start(
            turn_start_member,
            party=party,
            turn=1,
        )

        effects = turn_start_member.get_active_effects()
        synergy_effects = [e for e in effects if e.name == "advanced_combat_synergy_synergy_damage"]
        assert len(synergy_effects) == 1
        # Should be 3 allies * 5 = 15 bonus damage
        assert synergy_effects[0].stat_modifiers["atk"] == 15

    @pytest.mark.asyncio
    async def test_turn_start_insufficient_allies(self, registry, party_member):
        """Test turn_start doesn't trigger with insufficient living allies."""

        small_party = [party_member]  # Only 1 ally (self)

        await registry.trigger_turn_start(
            party_member,
            party=small_party,
            turn=1
        )

        effects = party_member.get_active_effects()
        synergy_effects = [e for e in effects if e.name == "advanced_combat_synergy_synergy_damage"]
        assert len(synergy_effects) == 0

    @pytest.mark.asyncio
    async def test_action_taken_stack_building(self, registry, party_member, party, target_foe):
        """Test that action_taken builds stacks and applies scaling effects."""

        # Create a member with action_taken behavior specifically
        action_member = Stats()
        action_member.id = "action_member"
        action_member.passives = ["advanced_combat_synergy"]

        passive_cls = registry._registry["advanced_combat_synergy"]

        # Take multiple actions to build stacks using the registry trigger
        for i in range(3):
            await registry.trigger(
                "action_taken",
                action_member,
                hit_target=target_foe,
                party=party,
            )

            # Check that stacks increased by checking the actual class from registry
            stacks = passive_cls.get_stacks(action_member)
            assert stacks == i + 1

            # Check that persistent effect updated
            effects = action_member.get_active_effects()
            persistent_effects = [
                e for e in effects if e.name == "advanced_combat_synergy_persistent_buff"
            ]
            assert len(persistent_effects) == 1

            expected_atk = (i + 1) * 3
            expected_crit = (i + 1) * 0.01
            assert persistent_effects[0].stat_modifiers["atk"] == expected_atk
            assert persistent_effects[0].stat_modifiers["crit_rate"] == expected_crit
            assert persistent_effects[0].duration == -1  # Permanent

    @pytest.mark.asyncio
    async def test_max_stacks_limit(self, registry, party_member, party, target_foe):
        """Test that stacks don't exceed max_stacks limit."""

        # Create a member for stack limit testing
        limit_member = Stats()
        limit_member.id = "limit_member"
        limit_member.passives = ["advanced_combat_synergy"]

        passive_cls = registry._registry["advanced_combat_synergy"]

        # Take more actions than max_stacks
        for _ in range(5):  # More than max_stacks of 3
            await registry.trigger(
                "action_taken",
                limit_member,
                hit_target=target_foe,
                party=party,
            )

        # Stacks should be capped at max_stacks, check using registry class
        stacks = passive_cls.get_stacks(limit_member)
        assert stacks == 3  # max_stacks

    @pytest.mark.asyncio
    async def test_backward_compatibility(self, registry):
        """Test that enhanced triggers maintain backward compatibility."""

        # Create a simple passive without enhanced context support
        simple_member = Stats()
        simple_member.id = "simple_member"
        simple_member.passives = ["luna_lunar_reservoir"]  # Existing simple passive

        # Should not raise error when called with enhanced context
        await registry.trigger(
            "action_taken",
            simple_member,
            party=[simple_member],
            foes=[],
            action_name="slash"
        )

        # Luna passive uses internal state tracking, so check that it was triggered
        from plugins.passives.normal.luna_lunar_reservoir import LunaLunarReservoir
        entity_id = id(simple_member)
        charge = LunaLunarReservoir._charge_points.get(entity_id, 0)
        assert charge > 0, "Luna passive should have accumulated charge"
        # Clean up
        LunaLunarReservoir._charge_points.clear()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
