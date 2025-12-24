"""Progression and leveling system for idle game.

This module handles experience distribution, level-up mechanics,
and reward generation. Adapted for tick-based gameplay.
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple


class ProgressionManager:
    """Manages character progression, leveling, and rewards.

    Handles experience gain calculation, level-up thresholds,
    stat growth on level-up, and reward distribution.
    """

    # Base experience required for level 2
    BASE_EXP_REQUIREMENT = 100

    # Exponential growth factor for exp requirements
    EXP_GROWTH_FACTOR = 1.15

    # Stat growth per level
    STAT_GROWTH_PER_LEVEL = {
        "max_hp": 10,
        "atk": 5,
        "defense": 5,
        "crit_rate": 0.001,  # 0.1% per level
        "crit_damage": 0.02,  # 2% per level
        "vitality": 0.01,
    }

    def __init__(self):
        """Initialize progression manager."""
        self.achievements: Dict[str, bool] = {}
        self.milestones: Dict[str, int] = {}

    def calculate_exp_required(self, level: int) -> int:
        """Calculate experience required to reach the next level.

        Args:
            level: Current level

        Returns:
            Experience points needed for next level
        """
        if level < 1:
            level = 1
        return int(self.BASE_EXP_REQUIREMENT * (self.EXP_GROWTH_FACTOR ** (level - 1)))

    def calculate_total_exp_for_level(self, target_level: int) -> int:
        """Calculate total experience needed to reach a target level from level 1.

        Args:
            target_level: Target level

        Returns:
            Total experience required
        """
        total = 0
        for lvl in range(1, target_level):
            total += self.calculate_exp_required(lvl)
        return total

    def check_level_up(self, current_level: int, current_exp: int) -> Tuple[bool, int, int]:
        """Check if a character should level up based on their experience.

        Args:
            current_level: Character's current level
            current_exp: Character's current experience points

        Returns:
            Tuple of (should_level_up, new_level, remaining_exp)
        """
        required_exp = self.calculate_exp_required(current_level)

        if current_exp >= required_exp:
            new_level = current_level + 1
            remaining_exp = current_exp - required_exp
            return True, new_level, remaining_exp

        return False, current_level, current_exp

    def apply_level_up(
        self,
        character_data: Dict[str, Any],
        new_level: int
    ) -> Dict[str, Any]:
        """Apply level-up stat growth to a character.

        Args:
            character_data: Character dictionary with stats
            new_level: The new level after leveling up

        Returns:
            Updated character data with new stats
        """
        if "runtime" not in character_data:
            character_data["runtime"] = {}

        runtime = character_data["runtime"]
        base_stats = character_data.get("base_stats", {})

        # Update level
        old_level = runtime.get("level", 1)
        runtime["level"] = new_level

        # Calculate levels gained (usually 1, but could be more for big exp gains)
        levels_gained = new_level - old_level

        # Apply stat growth for each level gained
        for stat, growth in self.STAT_GROWTH_PER_LEVEL.items():
            if stat in base_stats:
                current_value = base_stats[stat]
                base_stats[stat] = current_value + (growth * levels_gained)

        # Update max HP in runtime
        runtime["max_hp"] = base_stats.get("max_hp", 1000)

        # Heal to full on level up
        runtime["hp"] = runtime["max_hp"]

        return character_data

    def process_character_progression(
        self,
        character_data: Dict[str, Any],
        exp_gained: float
    ) -> List[Dict[str, Any]]:
        """Process experience gain and handle any level-ups.

        Args:
            character_data: Character dictionary
            exp_gained: Amount of experience gained this tick

        Returns:
            List of level-up events (empty if no level-ups occurred)
        """
        if "runtime" not in character_data:
            character_data["runtime"] = {"level": 1, "exp": 0}

        runtime = character_data["runtime"]
        runtime["exp"] = runtime.get("exp", 0) + exp_gained

        level_ups = []

        # Check for multiple level-ups in case of large exp gain
        while True:
            current_level = runtime.get("level", 1)
            current_exp = runtime.get("exp", 0)

            should_level, new_level, remaining_exp = self.check_level_up(
                current_level, current_exp
            )

            if not should_level:
                break

            # Apply level-up
            self.apply_level_up(character_data, new_level)
            runtime["exp"] = remaining_exp

            # Record level-up event
            level_ups.append({
                "character_id": character_data["id"],
                "old_level": current_level,
                "new_level": new_level,
                "stats_gained": self.STAT_GROWTH_PER_LEVEL.copy()
            })

        return level_ups

    def distribute_exp_solo(
        self,
        character_data: Dict[str, Any],
        base_exp: float,
        multiplier: float = 1.0
    ) -> float:
        """Calculate experience gain for solo (non-shared) mode.

        Args:
            character_data: Character receiving exp
            base_exp: Base experience amount
            multiplier: Additional multiplier (from combat boosts, etc.)

        Returns:
            Final experience amount to grant
        """
        char_exp_mult = character_data.get("runtime", {}).get("exp_multiplier", 1.0)
        return base_exp * char_exp_mult * multiplier

    def distribute_exp_shared(
        self,
        viewing_characters: List[Dict[str, Any]],
        base_exp: float,
        multipliers: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """Calculate experience distribution in shared exp mode.

        Args:
            viewing_characters: List of characters currently being viewed
            base_exp: Base experience amount
            multipliers: Optional per-character multipliers

        Returns:
            Dictionary mapping character_id to exp amount
        """
        if not viewing_characters:
            return {}

        if multipliers is None:
            multipliers = {}

        # Calculate shared bonus pool
        bonus_pool = 0.0
        for char in viewing_characters:
            char_mult = char.get("runtime", {}).get("exp_multiplier", 1.0)
            combat_mult = multipliers.get(char["id"], 1.0)
            bonus_pool += (char_mult * combat_mult) * 0.01

        # Distribute to each character
        exp_distribution = {}
        for char in viewing_characters:
            char_id = char["id"]
            char_mult = char.get("runtime", {}).get("exp_multiplier", 1.0)
            combat_mult = multipliers.get(char_id, 1.0)

            # Main exp (45% of normal rate) + shared bonus
            main_exp = (base_exp * char_mult * combat_mult) * 0.45
            final_exp = main_exp + bonus_pool

            exp_distribution[char_id] = final_exp

        return exp_distribution

    def generate_rewards(
        self,
        level: int,
        reward_type: str = "level_up"
    ) -> Dict[str, Any]:
        """Generate rewards based on progression milestones.

        Args:
            level: Character level triggering the reward
            reward_type: Type of reward to generate

        Returns:
            Dictionary containing reward data
        """
        rewards = {
            "gold": 0,
            "items": [],
            "cards": [],
            "relics": []
        }

        if reward_type == "level_up":
            # Gold reward scales with level
            rewards["gold"] = level * 10

            # Milestone rewards at levels 5, 10, 15, etc.
            if level % 5 == 0:
                rewards["items"].append(f"upgrade_material_t{min(level // 5, 4)}")

            # Special rewards at major milestones
            if level == 10:
                rewards["cards"].append("basic_attack_card")
            elif level == 20:
                rewards["relics"].append("novice_relic")

        return rewards

    def track_achievement(self, achievement_id: str) -> bool:
        """Mark an achievement as completed.

        Args:
            achievement_id: Unique identifier for the achievement

        Returns:
            True if newly completed, False if already completed
        """
        if achievement_id in self.achievements:
            return False

        self.achievements[achievement_id] = True
        return True

    def has_achievement(self, achievement_id: str) -> bool:
        """Check if an achievement has been completed."""
        return self.achievements.get(achievement_id, False)

    def update_milestone(self, milestone_id: str, value: int) -> None:
        """Update a milestone counter.

        Args:
            milestone_id: Unique identifier for the milestone
            value: New value for the milestone
        """
        self.milestones[milestone_id] = value

    def get_milestone(self, milestone_id: str) -> int:
        """Get current value of a milestone counter."""
        return self.milestones.get(milestone_id, 0)
