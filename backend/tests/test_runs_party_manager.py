from runs.party_manager import _describe_passives

from autofighter.stats import Stats


def test_describe_passives_returns_list():
    assert isinstance(_describe_passives(Stats()), list)
