from collections import Counter

from autofighter import gacha
from plugins import characters as player_plugins
from plugins.characters._base import PlayerBase
from plugins.characters.foe_base import FoeBase


def _expected_high_rarity_ids() -> dict[str, int]:
    expected: dict[str, int] = {}
    for name in getattr(player_plugins, "__all__", []):
        cls = getattr(player_plugins, name, None)
        if not isinstance(cls, type) or not issubclass(cls, PlayerBase):
            continue
        if issubclass(cls, FoeBase):
            continue
        rarity = getattr(cls, "gacha_rarity", 0)
        if rarity < 5:
            continue
        cid = getattr(cls, "id", name)
        expected.setdefault(cid, rarity)
    return expected


def test_gacha_high_rarity_pools_are_unique() -> None:
    five_star, six_star = gacha._build_pools()
    expected = _expected_high_rarity_ids()

    counts = Counter([*five_star, *six_star])
    assert counts, "expected at least one high-rarity character"
    assert set(counts) == set(expected)
    assert all(count == 1 for count in counts.values())

    expected_five = {cid for cid, rarity in expected.items() if rarity == 5}
    expected_six = {cid for cid, rarity in expected.items() if rarity == 6}

    assert set(five_star) == expected_five
    assert set(six_star) == expected_six
