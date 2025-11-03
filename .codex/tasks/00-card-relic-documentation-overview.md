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

All 102 tasks are currently **unassigned** and ready for implementation.

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

**Next Steps:**
Individual card and relic plugins need to be updated to provide actual content for the `full_about` and `summarized_about` fields. 

For relics with dynamic stacking (41 relics have custom `describe()` methods), contributors should:
1. Add `full_about` and `summarized_about` fields
2. Override `full_about_stacks(stacks)` to provide stack-specific formatting
3. Can reuse existing `describe(stacks)` logic by calling it from `full_about_stacks()`
4. Optionally remove old `describe()` method after migration

Until plugins are updated, they will display the default "Missing..." messages.

Status markers will be added by contributors as they begin work on each task.

## Audit Summary (2025-11-03)

**Audit Scope**: 15 tasks (13 cards + 1 relic + 1 overview)

**Overall Status**: ALL 14 PLUGIN TASKS APPROVED

### Cards Audited (13 total):
1. ✅ Overclock (81bef1fc) - APPROVED
2. ✅ Adamantine Band (57982535) - APPROVED
3. ✅ Energizing Tea (a4fa6c3f) - APPROVED
4. ✅ A Micro Blade (6a78f32b) - APPROVED (note: filename is micro_blade.py, not a_micro_blade.py)
5. ✅ Arc Lightning (5691759a) - APPROVED
6. ✅ Swift Bandanna (2d52b3a6) - APPROVED
7. ✅ Eclipse Theater Sigil (8496b802) - APPROVED
8. ✅ Elemental Spark (1da12886) - APPROVED
9. ✅ Dynamo Wristbands (d50ef349) - APPROVED
10. ✅ Critical Transfer (dc583e4a) - APPROVED
11. ✅ Arcane Repeater (06b42b65) - APPROVED
12. ✅ Balanced Diet (2f984135) - APPROVED
13. ✅ Rejuvenating Tonic (07d8b912) - APPROVED

### Relics Audited (1 total):
14. ✅ Blood Debt Tithe (1ff339ae) - APPROVED

### Audit Findings:
- **All 14 tasks properly implemented** with correct `full_about` and `summarized_about` fields
- **Zero legacy `about` fields found** - all properly migrated
- **Description format standards: 100% compliance**
  - All `summarized_about` fields use qualitative descriptions without numbers
  - All `full_about` fields include specific numbers and percentages
- **Code quality**: All implementations follow repository conventions
- **Accuracy**: All descriptions match actual plugin mechanics
- **Special implementations noted**:
  - Blood Debt Tithe: Sophisticated run-persistent state tracking
  - Eclipse Theater Sigil: Complex Light/Dark rotation mechanics
  - Overclock: Advanced async implementation with action timing refresh

### Minor Administrative Notes:
- Some task files had incomplete checkboxes despite complete implementations (now corrected)
- A Micro Blade task refers to "a_micro_blade.py" but actual file is "micro_blade.py" (acceptable, implementation is correct)

### Conclusion:
This batch represents high-quality work across 14 card and relic plugins. All documentation fields are properly implemented, tested, and ready for production use. The contributor(s) demonstrated strong understanding of the documentation format standards and game mechanics.

Requesting review from the Task Master for final approval of all 14 tasks.
