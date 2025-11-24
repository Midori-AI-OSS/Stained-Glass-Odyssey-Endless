from dataclasses import dataclass

from plugins.passives.normal.ryne_oracle_of_balance import RyneOracleOfBalance


@dataclass
class RyneOracleOfBalancePrime(RyneOracleOfBalance):
    """[PRIME] Oracle with higher balance caps and stronger surges."""

    plugin_type = "passive"
    id = "ryne_oracle_of_balance_prime"
    name = "Prime Oracle of Balance"
    trigger = [
        "battle_start",
        "turn_start",
        "action_taken",
        "hit_landed",
        "ultimate_used",
    ]
    stack_display = "pips"
    max_stacks = 180

    SOFT_CAP = 180
    POST_CAP_EFFICIENCY = 0.75

    OWNER_ATK_RATIO = 0.25
    OWNER_MITIGATION_RATIO = 0.22
    OWNER_EFFECT_RES_RATIO = 0.18
    OWNER_CRIT_RATIO = 0.08
    LUNA_ATK_RATIO = 0.16
    LUNA_MITIGATION_RATIO = 0.12
    LUNA_EFFECT_RES_RATIO = 0.12

    ACTION_GAIN = 3
    HIT_GAIN = 2
    ULTIMATE_GAIN = 6
    LUNA_HIT_GAIN = 3
    THRESHOLD = 5

    @classmethod
    def get_description(cls) -> str:
        return (
            "[PRIME] Builds balance faster and holds more of it (180 cap, 75% overflow). "
            "Surges draw more attack, mitigation, and resistance for Ryne and Luna, with quicker thresholds and larger entry bonuses."
        )

