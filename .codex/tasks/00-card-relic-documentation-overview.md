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

**Important:** The old `about` field should be removed and replaced with these two new fields.

**full_about:**
- Detailed description of mechanics
- Explain all triggers, interactions, and edge cases
- Include stacking behavior (for relics)
- Use clear, technical language

**summarized_about:**
- Brief 1-2 sentence description
- Suitable for in-game UI tooltips
- Focus on core functionality
- Use concise, player-friendly language

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

Status markers will be added by contributors as they begin work on each task.
