import pytest

from plugins.characters.carly import Carly
from plugins.characters.persona_ice import PersonaIce
from plugins.characters.persona_light_and_dark import PersonaLightAndDark


@pytest.mark.parametrize(
    ("character_cls", "expected_defense", "expected_hp", "expected_aggro"),
    [
        (Carly, 220, 1600, 0.35),
        (PersonaIce, 210, 1650, 0.33),
        (PersonaLightAndDark, 240, 1700, 0.4),
    ],
)
def test_tank_characters_have_elevated_baselines(
    character_cls,
    expected_defense,
    expected_hp,
    expected_aggro,
) -> None:
    character = character_cls()

    assert character.get_base_stat("mitigation") == pytest.approx(4.0)
    assert character.get_base_stat("defense") == pytest.approx(expected_defense)
    assert character.get_base_stat("max_hp") == pytest.approx(expected_hp)
    assert character.base_aggro == pytest.approx(expected_aggro)
