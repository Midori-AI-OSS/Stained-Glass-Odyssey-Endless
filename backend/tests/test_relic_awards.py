import pytest

from autofighter.party import Party
from autofighter.relics import apply_relics
from autofighter.relics import award_relic
from plugins.characters._base import PlayerBase


@pytest.mark.asyncio
async def test_award_relics_stack():
    party = Party()
    member = PlayerBase()
    member.set_base_stat('atk', 100)
    party.members.append(member)
    assert award_relic(party, "bent_dagger") is not None
    assert award_relic(party, "bent_dagger") is not None
    await apply_relics(party)
    assert party.relics == ["bent_dagger", "bent_dagger"]
    assert party.members[0].atk == int(100 * 1.03 * 1.03)
