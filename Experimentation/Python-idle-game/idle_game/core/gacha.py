"""Gacha system for character acquisition.

This module handles character pulls, rarity distribution, pity system,
banner rotation, and duplicate character handling. Adapted from backend
gacha system to work with JSON-based storage.
"""

from dataclasses import dataclass
import math
import random
import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from .save_manager import SaveManager

# Rarity constants
RARITY_COMMON = 1
RARITY_RARE = 2
RARITY_EPIC = 3
RARITY_LEGENDARY = 4
RARITY_5_STAR = 5
RARITY_6_STAR = 6

# Element types for upgrade items
ELEMENTS = ["fire", "water", "earth", "wind", "light", "dark"]

# Stats that can be upgraded with duplicates
UPGRADEABLE_STATS = [
    "max_hp",
    "atk",
    "defense",
    "crit_rate",
    "crit_damage",
    "vitality",
]

# Free stat levels granted per duplicate pull
FREE_DUPLICATE_LEVELS_PER_STAT = 5


def _calculate_next_cost(last_cost: int) -> int:
    """Calculate the cost for the next stat upgrade level.

    Args:
        last_cost: Cost of the previous upgrade

    Returns:
        Cost for next upgrade (5% increase)
    """
    if not last_cost or last_cost < 1:
        return 1
    return max(1, math.ceil(last_cost * 1.05))


@dataclass
class PullResult:
    """Result of a single gacha pull.

    Attributes:
        type: "character" or "item"
        id: Character ID or item ID
        rarity: Rarity tier (1-6)
        stacks: Number of duplicate stacks (for characters)
        stat_levels_awarded: Number of stat upgrade levels granted (for duplicates)
    """
    type: str
    id: str
    rarity: int
    stacks: Optional[int] = None
    stat_levels_awarded: Optional[int] = None


@dataclass
class Banner:
    """Gacha banner configuration.

    Attributes:
        id: Unique banner identifier
        name: Display name
        banner_type: "standard" or "custom"
        featured_character: ID of featured character (50% rate-up)
        start_time: Unix timestamp when banner starts
        end_time: Unix timestamp when banner ends
        active: Whether banner is currently active
    """
    id: str
    name: str
    banner_type: str
    featured_character: Optional[str] = None
    start_time: float = 0.0
    end_time: float = 0.0
    active: bool = True


class GachaManager:
    """Manages the gacha/pull system.

    Handles character acquisition through pulls, maintains pity counters,
    manages banner rotation, and processes duplicate characters into stat upgrades.
    """

    def __init__(self):
        """Initialize gacha manager with default state."""
        self._state = self._load_state()
        self._init_default_banners()

    def _load_state(self) -> Dict[str, Any]:
        """Load gacha state from save file."""
        state = SaveManager.load_setting("gacha_state", {})

        # Ensure all required keys exist
        state.setdefault("pity", 0)
        state.setdefault("items", {})
        state.setdefault("character_stacks", {})
        state.setdefault("owned_characters", [])
        state.setdefault("stat_upgrades", {})  # {char_id: {stat: [(level, cost), ...]}}
        state.setdefault("banners", [])

        return state

    def _save_state(self) -> None:
        """Save gacha state to file."""
        SaveManager.save_setting("gacha_state", self._state)

    def _init_default_banners(self) -> None:
        """Initialize default banners if they don't exist."""
        if self._state["banners"]:
            # Check if banners need rotation
            self._update_banner_rotation()
            return

        current_time = time.time()
        self._create_banner_rotation(current_time)

    def _create_banner_rotation(self, start_time: float) -> None:
        """Create initial rotating banner set.

        Args:
            start_time: Unix timestamp for rotation start
        """
        banner_duration = 86400 * 3  # 3 days

        # Standard banner (always available)
        banners = [
            {
                "id": "standard",
                "name": "Standard Warp",
                "banner_type": "standard",
                "featured_character": None,
                "start_time": 0,
                "end_time": 0,
                "active": True
            }
        ]

        # Create rotating custom banners
        # For now, use placeholder featured characters
        # In full implementation, this would scan character data
        custom_banners = [
            {
                "id": "custom1",
                "name": "Featured Character I",
                "banner_type": "custom",
                "featured_character": "becca",
                "start_time": start_time,
                "end_time": start_time + banner_duration,
                "active": True
            },
            {
                "id": "custom2",
                "name": "Featured Character II",
                "banner_type": "custom",
                "featured_character": "ally",
                "start_time": start_time + banner_duration,
                "end_time": start_time + (banner_duration * 2),
                "active": True
            }
        ]

        banners.extend(custom_banners)
        self._state["banners"] = banners
        self._save_state()

    def _update_banner_rotation(self) -> None:
        """Update expired banners with new featured characters."""
        current_time = time.time()
        banner_duration = 86400 * 3
        updated = False

        for banner in self._state["banners"]:
            if banner["banner_type"] == "custom" and banner["active"]:
                if current_time > banner["end_time"]:
                    # Rotate to new featured character
                    # In full implementation, select from available pool
                    banner["start_time"] = current_time
                    banner["end_time"] = current_time + banner_duration
                    updated = True

        if updated:
            self._save_state()

    def get_banners(self) -> List[Banner]:
        """Get all configured banners.

        Returns:
            List of Banner objects
        """
        return [
            Banner(
                id=b["id"],
                name=b["name"],
                banner_type=b["banner_type"],
                featured_character=b.get("featured_character"),
                start_time=b.get("start_time", 0),
                end_time=b.get("end_time", 0),
                active=b.get("active", True)
            )
            for b in self._state["banners"]
        ]

    def get_available_banners(self) -> List[Banner]:
        """Get currently available banners.

        Returns:
            List of active banners within their time windows
        """
        self._update_banner_rotation()
        current_time = time.time()
        available = []

        for banner in self.get_banners():
            if not banner.active:
                continue

            if banner.banner_type == "standard":
                available.append(banner)
            elif banner.start_time <= current_time <= banner.end_time:
                available.append(banner)

        return available

    def get_pity(self) -> int:
        """Get current pity counter."""
        return self._state["pity"]

    def _set_pity(self, value: int) -> None:
        """Set pity counter."""
        self._state["pity"] = value
        self._save_state()

    def get_items(self) -> Dict[str, int]:
        """Get upgrade items inventory."""
        return self._state["items"].copy()

    def _add_item(self, item_id: str, count: int = 1) -> None:
        """Add upgrade items to inventory."""
        current = self._state["items"].get(item_id, 0)
        self._state["items"][item_id] = current + count
        self._auto_craft_items()
        self._save_state()

    def _auto_craft_items(self) -> None:
        """Auto-craft lower tier items into higher tiers (up to 4★)."""
        items = self._state["items"]

        for element in ELEMENTS:
            for star in range(1, 4):  # 1★ to 3★ can craft up
                lower = f"{element}_{star}"
                higher = f"{element}_{star + 1}"

                while items.get(lower, 0) >= 125:
                    items[lower] -= 125
                    items[higher] = items.get(higher, 0) + 1

        # Clean up zero counts
        self._state["items"] = {k: v for k, v in items.items() if v > 0}

    def get_character_stacks(self, character_id: str) -> int:
        """Get duplicate stack count for a character.

        Args:
            character_id: Character ID

        Returns:
            Number of times character has been pulled
        """
        return self._state["character_stacks"].get(character_id, 0)

    def _add_character(self, character_id: str) -> tuple[int, int]:
        """Add a character to owned list or increment stacks.

        Args:
            character_id: Character ID

        Returns:
            Tuple of (new_stack_count, bonus_stat_levels_granted)
        """
        # Add to owned list if not already there
        if character_id not in self._state["owned_characters"]:
            self._state["owned_characters"].append(character_id)

        # Increment stacks
        current_stacks = self._state["character_stacks"].get(character_id, 0)
        new_stacks = current_stacks + 1
        self._state["character_stacks"][character_id] = new_stacks

        # Grant stat upgrades for duplicates (after first pull)
        bonus_levels = 0
        if current_stacks > 0:  # This is a duplicate
            bonus_levels = self._grant_duplicate_stat_levels(character_id)

        self._save_state()
        return new_stacks, bonus_levels

    def _grant_duplicate_stat_levels(self, character_id: str) -> int:
        """Grant free stat upgrade levels for duplicate character pull.

        Args:
            character_id: Character ID

        Returns:
            Total number of stat levels granted
        """
        if character_id not in self._state["stat_upgrades"]:
            self._state["stat_upgrades"][character_id] = {}

        char_upgrades = self._state["stat_upgrades"][character_id]
        total_levels = 0

        for stat in UPGRADEABLE_STATS:
            if stat not in char_upgrades:
                char_upgrades[stat] = []

            upgrades_list = char_upgrades[stat]

            # Get last cost
            last_cost = upgrades_list[-1][1] if upgrades_list else 0

            # Grant free levels
            for _ in range(FREE_DUPLICATE_LEVELS_PER_STAT):
                next_cost = _calculate_next_cost(last_cost)
                upgrade_percent = next_cost * 0.001
                upgrades_list.append((upgrade_percent, next_cost))
                last_cost = next_cost
                total_levels += 1

        return total_levels

    def _rarity_weights(self, pity: int) -> List[float]:
        """Calculate rarity weights based on pity counter.

        Higher pity increases chances of higher rarity items.

        Args:
            pity: Current pity count

        Returns:
            List of weights for rarities 1-4
        """
        factor = min(pity, 180) / 180
        return [
            0.10 * (1 - factor),  # 1★
            0.50 - 0.20 * factor,  # 2★
            0.30 + 0.20 * factor,  # 3★
            0.10 + 0.10 * factor,  # 4★
        ]

    def pull(
        self,
        count: int,
        banner_id: str = "standard",
        character_pool: Optional[List[Dict[str, Any]]] = None
    ) -> List[PullResult]:
        """Perform gacha pulls.

        Args:
            count: Number of pulls (1, 5, or 10)
            banner_id: ID of banner to pull from
            character_pool: Optional list of character data for rarity checking

        Returns:
            List of pull results
        """
        if count not in (1, 5, 10):
            raise ValueError("Pull count must be 1, 5, or 10")

        # Check for sufficient tickets
        tickets = self._state["items"].get("ticket", 0)
        if tickets < count:
            raise PermissionError("Insufficient tickets")

        # Deduct tickets
        self._state["items"]["ticket"] = tickets - count

        # Get banner
        banners = {b.id: b for b in self.get_available_banners()}
        banner = banners.get(banner_id)
        if not banner:
            raise ValueError("Banner not available")

        # Build character pools by rarity from character_pool if provided
        five_star = []
        six_star = []
        if character_pool:
            for char in character_pool:
                rarity = char.get("gacha_rarity", 0)
                char_id = char.get("id")
                if rarity == 5 and char_id:
                    five_star.append(char_id)
                elif rarity == 6 and char_id:
                    six_star.append(char_id)

        # Fallback pools if no character data provided
        if not five_star:
            five_star = ["becca", "ally"]
        if not six_star:
            six_star = ["luna"]

        results = []
        pity = self.get_pity()
        owned = set(self._state["owned_characters"])

        for _ in range(count):
            # 0.01% chance for 6★ character
            if random.random() < 0.0001:
                # Select 6★ character
                if banner.banner_type == "custom" and banner.featured_character in six_star:
                    if random.random() < 0.5:
                        char_id = banner.featured_character
                    else:
                        pool = [c for c in six_star if c not in owned and c != banner.featured_character]
                        char_id = random.choice(pool if pool else six_star)
                else:
                    pool = [c for c in six_star if c not in owned]
                    char_id = random.choice(pool if pool else six_star)

                stacks, stat_levels = self._add_character(char_id)
                owned.add(char_id)
                results.append(PullResult("character", char_id, 6, stacks, stat_levels or None))
                pity = 0
                continue

            # Pity-adjusted 5★ chance
            pity_chance = 0.00001 + pity * ((0.05 - 0.00001) / 159)
            if pity >= 179 or random.random() < pity_chance:
                # Select 5★ character
                if banner.banner_type == "custom" and banner.featured_character in five_star:
                    if random.random() < 0.5:
                        char_id = banner.featured_character
                    else:
                        pool = [c for c in five_star if c not in owned and c != banner.featured_character]
                        char_id = random.choice(pool if pool else five_star)
                else:
                    pool = [c for c in five_star if c not in owned]
                    char_id = random.choice(pool if pool else five_star)

                stacks, stat_levels = self._add_character(char_id)
                owned.add(char_id)
                results.append(PullResult("character", char_id, 5, stacks, stat_levels or None))
                pity = 0
            else:
                # Upgrade item drop
                weights = self._rarity_weights(pity)
                roll = random.random()
                threshold = 0.0
                rarity = 1

                for idx, weight in enumerate(weights, start=1):
                    threshold += weight
                    if roll < threshold:
                        rarity = idx
                        break

                element = random.choice(ELEMENTS)
                item_id = f"{element}_{rarity}"
                self._add_item(item_id)
                results.append(PullResult("item", item_id, rarity))
                pity += 1

        self._set_pity(pity)
        return results

    def get_state(self) -> Dict[str, Any]:
        """Get complete gacha state for UI display.

        Returns:
            Dictionary with pity, items, characters, and banners
        """
        self._update_banner_rotation()

        return {
            "pity": self._state["pity"],
            "items": self._state["items"].copy(),
            "owned_characters": self._state["owned_characters"].copy(),
            "character_stacks": self._state["character_stacks"].copy(),
            "banners": [
                {
                    "id": b.id,
                    "name": b.name,
                    "banner_type": b.banner_type,
                    "featured_character": b.featured_character,
                    "start_time": b.start_time,
                    "end_time": b.end_time
                }
                for b in self.get_available_banners()
            ]
        }
