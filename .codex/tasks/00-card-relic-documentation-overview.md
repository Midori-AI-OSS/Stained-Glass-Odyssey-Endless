# Card and Relic Documentation Project Overview

## Summary

This document provides an overview of the card and relic documentation enhancement project. Individual task files have been created for each card and relic to replace the old `about` field with new `full_about` and `summarized_about` fields.

## Objective

Add structured documentation fields to all cards and relics to enable:
- Better in-game tooltips and help text
- Future LLM-based features that need to understand card/relic mechanics
- Consistent documentation patterns across all plugins

## Task Distribution

### Cards (61 total)
All card task files are located in `.codex/tasks/cards/` with the naming pattern:
`{hash}-{card_name}-documentation.md`

Card list:
- a_micro_blade, adamantine_band, arc_lightning, arcane_repeater, balanced_diet
- battle_meditation, bulwark_totem, calm_beads, coated_armor, critical_focus
- critical_overdrive, critical_transfer, dynamo_wristbands, eclipse_theater_sigil
- elemental_spark, enduring_charm, enduring_will, energizing_tea, equilibrium_prism
- expert_manual, farsight_scope, flux_convergence, flux_paradox_engine, fortified_plating
- guardian_choir_circuit, guardian_shard, guardians_beacon, guiding_compass, honed_point
- inspiring_banner, iron_guard, iron_resolve, iron_resurgence, keen_goggles
- lightweight_boots, lucky_coin, mindful_tassel, mystic_aegis, oracle_prayer_charm
- overclock, phantom_ally, polished_shield, precision_sights, reality_split
- reinforced_cloak, rejuvenating_tonic, sharpening_stone, spiked_shield, steady_grip
- steel_bangles, sturdy_boots, sturdy_vest, supercell_conductor, swift_bandanna
- swift_footwork, tactical_kit, tempest_pathfinder, temporal_shield, thick_skin
- vital_core, vital_surge

### Relics (41 total)
All relic task files are located in `.codex/tasks/relics/` with the naming pattern:
`{hash}-{relic_name}-documentation.md`

Relic list:
- arcane_flask, bent_dagger, blood_debt_tithe, cataclysm_engine, catalyst_vials
- command_beacon, copper_siphon, echo_bell, echoing_drum, eclipse_reactor
- ember_stone, entropy_mirror, fallback_essence, featherweight_anklet, field_rations
- frost_sigil, graviton_locket, greed_engine, guardian_charm, herbal_charm
- killer_instinct, lucky_button, momentum_gyro, null_lantern, old_coin
- omega_core, paradox_hourglass, plague_harp, pocket_manual, rusty_buckle
- safeguard_prism, shiny_pebble, siege_banner, soul_prism, stellar_compass
- tattered_flag, threadbare_cloak, timekeepers_hourglass, travelers_charm
- vengeful_pendant, wooden_idol

## Implementation Guidelines

Each task includes:
1. **Objective** - Clear statement of what needs to be changed
2. **Background** - Context on why these fields are needed
3. **Task Details** - Specific file to modify and changes required (remove old `about`, add new fields)
4. **Guidelines** - Best practices for writing descriptions
5. **Example Structure** - Code example showing where fields should go
6. **Acceptance Criteria** - Checklist for completion

### Field Requirements

**Important:** The old `about` field has been removed from the base classes and replaced with these two new fields. The base classes now provide default "Missing..." messages.

**full_about:**
- Detailed description of mechanics
- Explain all triggers, interactions, and edge cases
- Include stacking behavior (for relics)
- Use clear, technical language
- Default: "Missing full card/relic description, please report this"

**summarized_about:**
- Brief 1-2 sentence description
- Suitable for in-game UI tooltips
- Focus on core functionality
- Use concise, player-friendly language
- Default: "Missing summarized card/relic description, please report this"
- **For relics**: Never includes stack-specific information (always shows base behavior)

**New Methods:**
- **CardBase**: `get_about_str()` - Returns appropriate string based on user settings
- **RelicBase**: `get_about_str(stacks: int = 1)` - Returns appropriate string with stack support
- **RelicBase**: `full_about_stacks(stacks: int)` - Override this to provide stack-specific formatting
- The methods automatically check the CONCISE_DESCRIPTIONS option
- When concise mode is enabled, returns `summarized_about` (no stack info)
- When concise mode is disabled, calls `full_about_stacks(stacks)` which can be overridden
- The old `preview_summary()` and `describe(stacks)` methods have been removed from base classes
- All code now uses `get_about_str()` to retrieve description strings

**For Relics with Dynamic Stack Descriptions:**
Relics that need to show different descriptions based on stack count (like showing "gains 50% more gold" for 1 stack vs "gains 75% more gold" for 2 stacks) should simply:
1. Override `full_about_stacks(stacks)` to return stack-specific formatted strings
2. Optionally keep the old `describe(stacks)` method for backward compatibility

**Example:**
```python
def full_about_stacks(self, stacks: int) -> str:
    """Provide stack-aware description."""
    gold = 50 + 25 * (stacks - 1)
    hp = 1 + 0.5 * (stacks - 1)
    return f"Party loses {hp:.1f}% HP per action, gains {gold:.0f}% more gold"
```

Or reuse existing describe method:
```python
def full_about_stacks(self, stacks: int) -> str:
    """Reuse existing describe logic."""
    return self.describe(stacks)
```

## Progress Tracking

Contributors should:
1. Pick a task file from `.codex/tasks/cards/` or `.codex/tasks/relics/`
2. Add status marker when work begins (per Task Master protocol)
3. Implement the changes following the guidelines
4. Test that the plugin still loads and functions
5. Update status marker to `ready for review` when complete
6. After approval, the task file can be closed/deleted

## Task Status

**COMPLETED ✅** - All card and relic documentation tasks have been finished, audited, and approved.

- **Cards:** 62/63 updated with `full_about` and `summarized_about` fields (only `__init__.py` excluded)
- **Relics:** 41/42 updated (only `event_horizon.py` pending - needs documentation fields added)
  
All 102 individual task files have been processed and closed.

**Base System Update (COMPLETED):**
- ✅ CardBase updated with `full_about` and `summarized_about` fields
- ✅ RelicBase updated with `full_about` and `summarized_about` fields
- ✅ Old `about` field removed from both base classes
- ✅ Old `preview_summary()` method removed from both base classes
- ✅ Old `describe(stacks)` method removed from RelicBase (but individual relics can still have it)
- ✅ New `get_about_str()` method added to CardBase
- ✅ New `get_about_str(stacks)` method added to RelicBase with stack support
- ✅ New `full_about_stacks(stacks)` method added to RelicBase as override point for plugins
- ✅ All backend routes updated to use new method with stack information
- ✅ Default "Missing..." messages set for all plugins
- ✅ Stack information properly passed through all call sites

**Remaining Work:**

Only one relic still needs documentation fields added:
- **event_horizon.py** - Uses old `about` field, needs migration to `full_about` and `summarized_about`

This relic was recently implemented and wasn't part of the original documentation task set. A new task should be created for this final update.
