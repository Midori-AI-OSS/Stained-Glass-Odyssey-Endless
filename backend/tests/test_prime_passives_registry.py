from autofighter.passives import PassiveRegistry
from autofighter.passives import apply_rank_passives

PRIME_VARIANTS = {
    "advanced_combat_synergy": "advanced_combat_synergy_prime",
    "ally_overload": "ally_overload_prime",
    "becca_menagerie_bond": "becca_menagerie_bond_prime",
    "bubbles_bubble_burst": "bubbles_bubble_burst_prime",
    "carly_guardians_aegis": "carly_guardians_aegis_prime",
    "casno_phoenix_respite": "casno_phoenix_respite_prime",
    "graygray_counter_maestro": "graygray_counter_maestro_prime",
    "hilander_critical_ferment": "hilander_critical_ferment_prime",
    "ixia_tiny_titan": "ixia_tiny_titan_prime",
    "kboshi_flux_cycle": "kboshi_flux_cycle_prime",
    "lady_darkness_eclipsing_veil": "lady_darkness_eclipsing_veil_prime",
    "lady_echo_resonant_static": "lady_echo_resonant_static_prime",
    "lady_fire_and_ice_duality_engine": "lady_fire_and_ice_duality_engine_prime",
    "lady_lightning_stormsurge": "lady_lightning_stormsurge_prime",
    "lady_light_radiant_aegis": "lady_light_radiant_aegis_prime",
    "lady_of_fire_infernal_momentum": "lady_of_fire_infernal_momentum_prime",
    "lady_storm_supercell": "lady_storm_supercell_prime",
    "lady_wind_tempest_guard": "lady_wind_tempest_guard_prime",
    "luna_lunar_reservoir": "luna_lunar_reservoir_prime",
    "mezzy_gluttonous_bulwark": "mezzy_gluttonous_bulwark_prime",
    "persona_ice_cryo_cycle": "persona_ice_cryo_cycle_prime",
    "persona_light_and_dark_duality": "persona_light_and_dark_duality_prime",
    "player_level_up_bonus": "player_level_up_bonus_prime",
    "ryne_oracle_of_balance": "ryne_oracle_of_balance_prime",
}


def test_prime_passives_registered():
    registry = PassiveRegistry()._registry
    for base_id, prime_id in PRIME_VARIANTS.items():
        assert prime_id in registry, f"Missing prime passive for {base_id}"
        cls = registry[prime_id]
        assert getattr(cls, "plugin_type", None) == "passive"


def test_apply_rank_passives_maps_prime_variants():
    class Dummy:
        pass

    for base_id, prime_id in PRIME_VARIANTS.items():
        foe = Dummy()
        foe.rank = "prime"
        foe.passives = [base_id]
        apply_rank_passives(foe)
        assert prime_id in foe.passives

