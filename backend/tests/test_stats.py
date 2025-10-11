import pytest

from autofighter.stats import Stats
from autofighter.stats import get_enrage_percent
from autofighter.stats import set_enrage_percent


@pytest.mark.asyncio
async def test_apply_healing_minimum_one_with_low_vitality():
    previous_enrage = get_enrage_percent()
    try:
        set_enrage_percent(0.5)
        healer = Stats()
        target = Stats()

        target.max_hp = 20
        target.hp = 5

        healer.vitality = 0.2
        target.vitality = 0.3

        healed = await target.apply_healing(1, healer=healer)

        assert healed == 1
        assert target.hp == 6
    finally:
        set_enrage_percent(previous_enrage)
