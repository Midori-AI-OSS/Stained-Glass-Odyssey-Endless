from __future__ import annotations

from dataclasses import dataclass
import random
import time
from typing import Any

from plugins import players as player_plugins
from plugins.damage_types import ALL_DAMAGE_TYPES

from .save_manager import SaveManager


def _build_pools() -> tuple[list[str], list[str]]:
    five: list[str] = []
    six: list[str] = []
    for name in getattr(player_plugins, "__all__", []):
        cls = getattr(player_plugins, name)
        rarity = getattr(cls, "gacha_rarity", 0)
        cid = getattr(cls, "id", name)
        if cid in {"player", "luna", "mimic"}:
            continue
        if rarity == 5:
            five.append(cid)
        elif rarity == 6:
            six.append(cid)
    return five, six


FIVE_STAR, SIX_STAR = _build_pools()
ELEMENTS = [e.lower() for e in ALL_DAMAGE_TYPES]


@dataclass
class PullResult:
    type: str
    id: str
    rarity: int
    stacks: int | None = None


@dataclass
class Banner:
    id: str
    name: str
    banner_type: str  # "custom" or "standard"
    featured_character: str | None = None
    start_time: float = 0.0
    end_time: float = 0.0
    active: bool = True


class GachaManager:
    def __init__(self, save: SaveManager) -> None:
        self.save = save
        with self.save.connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS player_stacks (id TEXT PRIMARY KEY, stacks INTEGER NOT NULL)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS options (key TEXT PRIMARY KEY, value TEXT)"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS banners (id TEXT PRIMARY KEY, name TEXT, banner_type TEXT, featured_character TEXT, start_time REAL, end_time REAL, active INTEGER)"
            )
        self._init_default_banners()

    def _init_default_banners(self) -> None:
        """Initialize default banners if they don't exist."""
        current_time = time.time()

        with self.save.connection() as conn:
            # Check if banners already exist
            cur = conn.execute("SELECT COUNT(*) FROM banners")
            if cur.fetchone()[0] > 0:
                # Update banner rotation if needed
                self._update_banner_rotation()
                return

            # Create default banners with rotation
            self._create_banner_rotation(current_time)

    def _create_banner_rotation(self, start_time: float) -> None:
        """Create a rotating set of banners."""
        # Get all available 5★ and 6★ characters for rotation
        featured_pool = []
        for name in getattr(player_plugins, "__all__", []):
            cls = getattr(player_plugins, name)
            rarity = getattr(cls, "gacha_rarity", 0)
            cid = getattr(cls, "id", name)
            if cid not in {"player", "luna", "mimic"} and rarity >= 5:
                featured_pool.append(cid)

        if not featured_pool:
            featured_pool = ["becca", "ally"]  # Fallback

        owned_characters = self._get_owned()
        owned_pool = [cid for cid in featured_pool if cid in owned_characters]
        unowned_pool = [cid for cid in featured_pool if cid not in owned_characters]
        available_characters = set(featured_pool)
        selected_characters: list[str] = []

        def pick_character(preferred: list[str], alternate: list[str]) -> str:
            pool = [cid for cid in preferred if cid in available_characters]
            if not pool:
                pool = [cid for cid in alternate if cid in available_characters]
            if not pool:
                pool = [cid for cid in available_characters]
            if pool:
                choice = random.choice(pool)
                available_characters.discard(choice)
                selected_characters.append(choice)
                return choice
            if selected_characters:
                return selected_characters[0]
            return random.choice(featured_pool)

        # Create 3-day rotating banners
        banner_duration = 86400 * 3  # 3 days in seconds

        banners = [
            Banner("standard", "Standard Warp", "standard", None, 0, 0, True),
        ]

        # Create rotating custom banners
        custom_slots = [
            ("custom1", "Featured Character I", unowned_pool, owned_pool),
            ("custom2", "Featured Character II", owned_pool, unowned_pool),
        ]

        for index, (banner_id, banner_name, preferred_pool, alternate_pool) in enumerate(custom_slots):
            featured_character = pick_character(preferred_pool, alternate_pool)
            banner_start = start_time + (index * banner_duration)
            banner_end = banner_start + banner_duration

            banners.append(Banner(
                banner_id,
                banner_name,
                "custom",
                featured_character,
                banner_start,
                banner_end,
                True
            ))

        with self.save.connection() as conn:
            for banner in banners:
                conn.execute(
                    "INSERT INTO banners (id, name, banner_type, featured_character, start_time, end_time, active) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (banner.id, banner.name, banner.banner_type, banner.featured_character, banner.start_time, banner.end_time, 1 if banner.active else 0)
                )

    def _update_banner_rotation(self) -> None:
        """Update banner rotation if banners have expired."""
        current_time = time.time()

        # Get all available characters for rotation
        featured_pool = []
        for name in getattr(player_plugins, "__all__", []):
            cls = getattr(player_plugins, name)
            rarity = getattr(cls, "gacha_rarity", 0)
            cid = getattr(cls, "id", name)
            if cid not in {"player", "luna", "mimic"} and rarity >= 5:
                featured_pool.append(cid)

        if not featured_pool:
            return  # No characters to rotate

        owned_characters = self._get_owned()
        owned_pool = [cid for cid in featured_pool if cid in owned_characters]
        unowned_pool = [cid for cid in featured_pool if cid not in owned_characters]

        banner_duration = 86400 * 3  # 3 days

        with self.save.connection() as conn:
            # Check for expired custom banners
            cur = conn.execute(
                "SELECT id, featured_character, end_time FROM banners WHERE banner_type = 'custom' AND active = 1 ORDER BY id"
            )
            expired_banners = []

            banner_rows = cur.fetchall()

            for row in banner_rows:
                banner_id, featured_char, end_time = row
                if current_time > end_time:
                    expired_banners.append((banner_id, featured_char))

            if not expired_banners:
                return

            locked_characters = {
                featured_char
                for banner_id, featured_char, end_time in banner_rows
                if banner_id not in {banner for banner, _ in expired_banners} and featured_char
            }
            available_characters = {cid for cid in featured_pool if cid not in locked_characters}
            if not available_characters:
                available_characters = set(featured_pool)
            selected_characters: list[str] = []

            def pick_character(preferred: list[str], alternate: list[str], old_char: str | None) -> str | None:
                pool = [
                    cid for cid in preferred
                    if cid in available_characters and cid != old_char
                ]
                if not pool:
                    pool = [
                        cid for cid in alternate
                        if cid in available_characters and cid != old_char
                    ]
                if not pool:
                    pool = [cid for cid in available_characters if cid != old_char]
                if pool:
                    choice = random.choice(pool)
                    available_characters.discard(choice)
                    selected_characters.append(choice)
                    return choice
                if selected_characters:
                    return selected_characters[0]
                return old_char

            preference_map = {
                "custom1": (unowned_pool, owned_pool),
                "custom2": (owned_pool, unowned_pool),
            }

            for banner_id, old_char in expired_banners:
                preferred_pool, alternate_pool = preference_map.get(
                    banner_id,
                    (unowned_pool, owned_pool),
                )
                new_char = pick_character(preferred_pool, alternate_pool, old_char)
                new_start = current_time
                new_end = current_time + banner_duration

                if new_char:
                    conn.execute(
                        "UPDATE banners SET featured_character = ?, start_time = ?, end_time = ? WHERE id = ?",
                        (new_char, new_start, new_end, banner_id)
                    )
                else:
                    conn.execute(
                        "UPDATE banners SET start_time = ?, end_time = ? WHERE id = ?",
                        (new_start, new_end, banner_id)
                    )

    def get_banners(self) -> list[Banner]:
        """Get all available banners."""
        with self.save.connection() as conn:
            cur = conn.execute("SELECT id, name, banner_type, featured_character, start_time, end_time, active FROM banners ORDER BY banner_type, id")
            banners = []
            for row in cur.fetchall():
                banners.append(Banner(
                    id=row[0],
                    name=row[1],
                    banner_type=row[2],
                    featured_character=row[3],
                    start_time=row[4],
                    end_time=row[5],
                    active=bool(row[6])
                ))
            return banners

    def get_active_banner(self, banner_id: str) -> Banner | None:
        """Get a specific active banner."""
        banners = self.get_banners()
        current_time = time.time()

        for banner in banners:
            if banner.id == banner_id and banner.active:
                if banner.banner_type == "standard":
                    return banner
                elif banner.start_time <= current_time <= banner.end_time:
                    return banner
        return None

    def get_available_banners(self) -> list[Banner]:
        """Get all currently available banners."""
        banners = self.get_banners()
        current_time = time.time()
        available = []

        for banner in banners:
            if banner.active:
                if banner.banner_type == "standard":
                    available.append(banner)
                elif banner.start_time <= current_time <= banner.end_time:
                    available.append(banner)

        return available

    def get_featured_characters(self) -> list[dict[str, Any]]:
        """Get character information for all featured characters in active banners."""
        banners = self.get_available_banners()
        featured_chars = []

        for banner in banners:
            if banner.featured_character:
                # Get character info
                for name in getattr(player_plugins, "__all__", []):
                    cls = getattr(player_plugins, name)
                    if getattr(cls, "id", name) == banner.featured_character:
                        featured_chars.append({
                            "id": banner.featured_character,
                            "name": getattr(cls, "name", banner.featured_character),
                            "about": getattr(cls, "about", "Character description placeholder"),
                            "gacha_rarity": getattr(cls, "gacha_rarity", 5),
                            "char_type": str(getattr(cls, "char_type", "C")),
                            "banner_id": banner.id
                        })
                        break

        return featured_chars

    def _get_pity(self) -> int:
        with self.save.connection() as conn:
            cur = conn.execute(
                "SELECT value FROM options WHERE key = ?", ("gacha_pity",)
            )
            row = cur.fetchone()
            return int(row[0]) if row else 0

    def _set_pity(self, value: int) -> None:
        with self.save.connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO options (key, value) VALUES (?, ?)",
                ("gacha_pity", str(value)),
            )

    def _get_items(self) -> dict[str, int]:
        with self.save.connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS upgrade_items (id TEXT PRIMARY KEY, count INTEGER NOT NULL)"
            )
            cur = conn.execute("SELECT id, count FROM upgrade_items")
            return {row[0]: int(row[1]) for row in cur.fetchall()}

    def _set_items(self, items: dict[str, int]) -> None:
        with self.save.connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS upgrade_items (id TEXT PRIMARY KEY, count INTEGER NOT NULL)"
            )
            for key, value in items.items():
                conn.execute(
                    "INSERT OR REPLACE INTO upgrade_items (id, count) VALUES (?, ?)",
                    (key, int(value)),
                )
            conn.execute("DELETE FROM upgrade_items WHERE count <= 0")

    def _get_auto_craft(self) -> bool:
        return True

    def _auto_craft(self, items: dict[str, int]) -> None:
        """Convert excess upgrade items into higher tiers.

        Crafting never creates items above 4★. Any surplus 4★ items remain at
        that tier so drop rate bonuses cannot raise the star level beyond the
        intended cap.
        """

        for element in ELEMENTS:
            for star in range(1, 4):
                lower = f"{element}_{star}"
                higher = f"{element}_{star + 1}"
                while items.get(lower, 0) >= 125:
                    items[lower] -= 125
                    items[higher] = items.get(higher, 0) + 1

        for key in [k for k, v in items.items() if v == 0]:
            del items[key]

    def craft(self) -> dict[str, int]:
        items = self._get_items()
        self._auto_craft(items)
        self._set_items(items)
        return items

    def _add_character(self, cid: str) -> int:
        with self.save.connection() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO owned_players (id) VALUES (?)",
                (cid,),
            )
            cur = conn.execute(
                "SELECT stacks FROM player_stacks WHERE id = ?", (cid,)
            )
            row = cur.fetchone()
            stacks = int(row[0]) + 1 if row else 1
            conn.execute(
                "INSERT OR REPLACE INTO player_stacks (id, stacks) VALUES (?, ?)",
                (cid, stacks),
            )
        return stacks

    def _get_owned(self) -> set[str]:
        with self.save.connection() as conn:
            cur = conn.execute("SELECT id FROM owned_players")
            return {row[0] for row in cur.fetchall()}

    def _rarity_weights(self, pity: int) -> list[float]:
        factor = min(pity, 180) / 180
        return [
            0.10 * (1 - factor),
            0.50 - 0.20 * factor,
            0.30 + 0.20 * factor,
            0.10 + 0.10 * factor,
        ]

    def pull(self, count: int, banner_id: str = "standard") -> list[PullResult]:
        if count not in (1, 5, 10):
            raise ValueError("invalid pull count")

        banner = self.get_active_banner(banner_id)
        if not banner:
            raise ValueError("banner not available")

        # Ensure tickets are decremented atomically in the database to avoid
        # any chance of stale in-memory state during multi-pull operations.
        with self.save.connection() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS upgrade_items (id TEXT PRIMARY KEY, count INTEGER NOT NULL)"
            )
            cur = conn.execute(
                "SELECT count FROM upgrade_items WHERE id = ?", ("ticket",)
            )
            row = cur.fetchone()
            current = int(row[0]) if row else 0
            if current < count:
                raise PermissionError("insufficient tickets")
            new_count = current - count
            # Upsert the new ticket count (0 removes later via cleanup)
            conn.execute(
                "INSERT OR REPLACE INTO upgrade_items (id, count) VALUES (?, ?)",
                ("ticket", new_count),
            )

        results: list[PullResult] = []
        pity = self._get_pity()
        # Re-load items after atomic decrement so downstream logic persists the
        # updated ticket count alongside new rewards.
        items = self._get_items()
        owned = self._get_owned()

        for _ in range(count):
            if random.random() < 0.0001:
                # 6★ character pull
                if banner.banner_type == "custom" and banner.featured_character and banner.featured_character in SIX_STAR:
                    # Featured 6★ character has higher chance
                    if random.random() < 0.5:
                        cid = banner.featured_character
                    else:
                        pool = [c for c in SIX_STAR if c not in owned and c != banner.featured_character]
                        cid = random.choice(pool or SIX_STAR)
                else:
                    pool = [c for c in SIX_STAR if c not in owned]
                    cid = random.choice(pool or SIX_STAR)
                stacks = self._add_character(cid)
                owned.add(cid)
                results.append(PullResult("character", cid, 6, stacks))
                pity = 0
                continue

            pity_chance = 0.00001 + pity * ((0.05 - 0.00001) / 159)
            if pity >= 179 or random.random() < pity_chance:
                # 5★ character pull
                if banner.banner_type == "custom" and banner.featured_character and banner.featured_character in FIVE_STAR:
                    # Featured 5★ character has 50% chance
                    if random.random() < 0.5:
                        cid = banner.featured_character
                    else:
                        pool = [c for c in FIVE_STAR if c not in owned and c != banner.featured_character]
                        cid = random.choice(pool or FIVE_STAR)
                else:
                    pool = [c for c in FIVE_STAR if c not in owned]
                    cid = random.choice(pool or FIVE_STAR)
                stacks = self._add_character(cid)
                owned.add(cid)
                results.append(PullResult("character", cid, 5, stacks))
                pity = 0
            else:
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
                key = f"{element}_{rarity}"
                items[key] = items.get(key, 0) + 1
                self._auto_craft(items)
                results.append(PullResult("item", key, rarity))
                pity += 1
        self._set_pity(pity)
        self._set_items(items)
        return results

    def get_state(self) -> dict[str, Any]:
        # Check for banner rotation updates before returning state
        self._update_banner_rotation()

        pity = self._get_pity()
        items = self._get_items()
        with self.save.connection() as conn:
            cur = conn.execute(
                "SELECT p.id, COALESCE(s.stacks, 0) FROM owned_players p LEFT JOIN player_stacks s ON p.id = s.id"
            )
            players = [
                {"id": row[0], "stacks": row[1]} for row in cur.fetchall()
            ]

        banners = self.get_available_banners()
        featured_characters = self.get_featured_characters()

        return {
            "pity": pity,
            "items": items,
            "players": players,
            "banners": [{"id": b.id, "name": b.name, "banner_type": b.banner_type, "featured_character": b.featured_character, "start_time": b.start_time, "end_time": b.end_time} for b in banners],
            "featured_characters": featured_characters,
        }
