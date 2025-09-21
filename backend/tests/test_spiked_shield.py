import asyncio

from autofighter.cards import apply_cards
from autofighter.cards import award_card
from autofighter.party import Party
from autofighter.stats import BUS
from autofighter.stats import Stats
from plugins.players._base import PlayerBase


def setup_event_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop


def test_spiked_shield_retaliates_damage(monkeypatch):
    loop = setup_event_loop()
    party = Party()
    defender = PlayerBase()
    attacker = PlayerBase()
    defender.set_base_stat('atk', 100)
    attacker.hp = attacker.set_base_stat('max_hp', 1000)
    party.members.append(defender)
    award_card(party, "spiked_shield")
    loop.run_until_complete(apply_cards(party))

    async def fake_apply_damage(self, amount, attacker=None, *, trigger_on_hit=True, action_name=None):
        self.hp -= amount
        return amount

    monkeypatch.setattr(Stats, "apply_damage", fake_apply_damage, raising=False)

    await BUS.emit_async("mitigation_triggered", defender, 100, 50, attacker)
    loop.run_until_complete(asyncio.sleep(0))

    assert attacker.hp == 1000 - int(defender.atk * 0.03)