# Comprehensive Ability Audit Summary

## Overview

This audit systematically examined all ultimate abilities, passives, characters, cards, and relics in the repository to verify that their implementations match their documented behavior.

## Methodology

The audit process involved:

1. **Automated Discovery**: Scanning all plugin directories for ability definitions
2. **AST Analysis**: Parsing Python source code to extract implementation details
3. **Documentation Extraction**: Gathering claims from docstrings, comments, and `about` fields
4. **Behavioral Comparison**: Comparing documented claims against actual code behavior
5. **Issue Classification**: Categorizing discrepancies by severity and type

## Scope

- **Total Abilities Audited**: 122
- **Cards**: 51
- **Chars**: 17
- **Passives**: 20
- **Relics**: 27
- **Ults**: 7

## Audit Results

**Total Issues Found**: 143

### Issues by Severity

- **Critical**: 0
- **High**: 36
- **Medium**: 93
- **Low**: 14

### Issues by Type

- **Card**: 64
- **Char**: 21
- **Passive**: 6
- **Relic**: 51
- **Ult**: 1

### Detailed Issues

#### 1. LadyDarkness (char)

**Severity**: medium

**Description**: Claims to trigger on 'any battlefield'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/lady_darkness.py`

---

#### 2. LadyDarkness (char)

**Severity**: medium

**Description**: Claims to trigger on 'enemies'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/lady_darkness.py`

---

#### 3. Luna (char)

**Severity**: medium

**Description**: Claims to trigger on 'steel is required'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/luna.py`

---

#### 4. Luna (char)

**Severity**: medium

**Description**: Claims to trigger on 'at her shoulder'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/luna.py`

---

#### 5. Luna (char)

**Severity**: medium

**Description**: Claims to trigger on 'begins'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/luna.py`

---

#### 6. Hilander (char)

**Severity**: medium

**Description**: Claims to trigger on 'he brings to crafting the perfect ale'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/hilander.py`

---

#### 7. Hilander (char)

**Severity**: medium

**Description**: Claims to trigger on 'of pressure'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/hilander.py`

---

#### 8. Becca (char)

**Severity**: medium

**Description**: Claims to trigger on 'bot taught her to create beauty from chaos'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/becca.py`

---

#### 9. Becca (char)

**Severity**: medium

**Description**: Claims to trigger on 'that makes her tactical arrangements as elegant as they are devastating'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/becca.py`

---

#### 10. LadyLight (char)

**Severity**: medium

**Description**: Claims to trigger on 'with her fellow fighters'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/lady_light.py`

---

#### 11. Mimic (char)

**Severity**: medium

**Description**: Claims to trigger on 'of whatever combat style it encounters'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/mimic.py`

---

#### 12. LadyOfFire (char)

**Severity**: medium

**Description**: Claims to trigger on 'into her fire magic'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/lady_of_fire.py`

---

#### 13. Bubbles (char)

**Severity**: medium

**Description**: Claims to trigger on 'they inevitably pop'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/bubbles.py`

---

#### 14. Mezzy (char)

**Severity**: medium

**Description**: Claims to trigger on 'of'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/mezzy.py`

---

#### 15. LadyEcho (char)

**Severity**: medium

**Description**: Claims to trigger on 'the price is measured in lost time'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/lady_echo.py`

---

#### 16. LadyEcho (char)

**Severity**: medium

**Description**: Claims to trigger on 'for building and creating'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/lady_echo.py`

---

#### 17. LadyEcho (char)

**Severity**: medium

**Description**: Claims to trigger on 'drives her inventive nature as she seeks to build devices that might mitigate or reverse the de'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/lady_echo.py`

---

#### 18. Kboshi (char)

**Severity**: medium

**Description**: Claims to trigger on 'and destruction'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/kboshi.py`

---

#### 19. Kboshi (char)

**Severity**: medium

**Description**: Claims to trigger on 'doesn'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/kboshi.py`

---

#### 20. Graygray (char)

**Severity**: medium

**Description**: Claims to trigger on 'in superior combat technique'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/graygray.py`

---

#### 21. Graygray (char)

**Severity**: medium

**Description**: Claims to trigger on 'into the very notes of their defeat'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/players/graygray.py`

---

#### 22. Advanced Combat Synergy (passive)

**Severity**: high

**Description**: Claims 50% HP effect

**Observed Behavior**: No hp effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/passives/advanced_combat_synergy.py`

---

#### 23. Advanced Combat Synergy (passive)

**Severity**: medium

**Description**: Claims to trigger on 'and cross'

**Observed Behavior**: No matching trigger found in code. Code triggers: ['hit_landed', 'turn_start', 'action_taken']

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/passives/advanced_combat_synergy.py`

---

#### 24. Gluttonous Bulwark (passive)

**Severity**: medium

**Description**: Claims to trigger on 'and stat siphoning'

**Observed Behavior**: No matching trigger found in code. Code triggers: ['turn_start']

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/passives/mezzy_gluttonous_bulwark.py`

---

#### 25. Counter Maestro (passive)

**Severity**: medium

**Description**: Claims to trigger on 'every hit taken'

**Observed Behavior**: No matching trigger found in code. Code triggers: ['damage_taken']

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/passives/graygray_counter_maestro.py`

---

#### 26. Critical Ferment (passive)

**Severity**: medium

**Description**: Claims to trigger on 'crit'

**Observed Behavior**: No matching trigger found in code. Code triggers: ['hit_landed']

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/passives/hilander_critical_ferment.py`

---

#### 27. Tiny Titan (passive)

**Severity**: high

**Description**: Claims 500% Vitality effect

**Observed Behavior**: No vitality effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/passives/ixia_tiny_titan.py`

---

#### 28. Energizing Tea (card)

**Severity**: medium

**Description**: Claims to trigger on 'the first turn'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/energizing_tea.py`

---

#### 29. Swift Bandanna (card)

**Severity**: medium

**Description**: Claims +1% crit effect

**Observed Behavior**: Code implements 0.03 (3.0%) for crit

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/swift_bandanna.py`

---

#### 30. Swift Bandanna (card)

**Severity**: medium

**Description**: Claims to trigger on 'dodge'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/swift_bandanna.py`

---

#### 31. Farsight Scope (card)

**Severity**: high

**Description**: Claims 50% HP effect

**Observed Behavior**: No hp effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/farsight_scope.py`

---

#### 32. Farsight Scope (card)

**Severity**: medium

**Description**: Claims +6% crit effect

**Observed Behavior**: Code implements 0.03 (3.0%) for crit

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/farsight_scope.py`

---

#### 33. Vital Surge (card)

**Severity**: medium

**Description**: Claims 50% HP effect

**Observed Behavior**: Code implements 0.55 (55.0%) for hp

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/vital_surge.py`

---

#### 34. Vital Surge (card)

**Severity**: high

**Description**: Claims +55% ATK effect

**Observed Behavior**: No atk effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/vital_surge.py`

---

#### 35. Phantom Ally (card)

**Severity**: medium

**Description**: Claims to trigger on 'the first turn'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/phantom_ally.py`

---

#### 36. Phantom Ally (card)

**Severity**: medium

**Description**: Claims to trigger on 'a permanent copy of a random ally'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/phantom_ally.py`

---

#### 37. Reinforced Cloak (card)

**Severity**: medium

**Description**: Claims to trigger on 'of long debuffs by 1'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/reinforced_cloak.py`

---

#### 38. Iron Resolve (card)

**Severity**: medium

**Description**: Claims 30% HP effect

**Observed Behavior**: Code implements 2.4 (240.0%) for hp

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/iron_resolve.py`

---

#### 39. Iron Resolve (card)

**Severity**: medium

**Description**: Claims 30% HP effect

**Observed Behavior**: Code implements 2.4 (240.0%) for hp

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/iron_resolve.py`

---

#### 40. Bulwark Totem (card)

**Severity**: medium

**Description**: Claims to trigger on 'an ally would die'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/bulwark_totem.py`

---

#### 41. Iron Resurgence (card)

**Severity**: medium

**Description**: Claims 10% HP effect

**Observed Behavior**: Code implements 2.0 (200.0%) for hp

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/iron_resurgence.py`

---

#### 42. Spiked Shield (card)

**Severity**: medium

**Description**: Claims to trigger on 'mitigation triggers'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/spiked_shield.py`

---

#### 43. Spiked Shield (card)

**Severity**: medium

**Description**: Claims to trigger on 'triggers'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/spiked_shield.py`

---

#### 44. Coated Armor (card)

**Severity**: high

**Description**: Claims 1% HP effect

**Observed Behavior**: No hp effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/coated_armor.py`

---

#### 45. Coated Armor (card)

**Severity**: medium

**Description**: Claims to trigger on 'mitigation reduces incoming damage'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/coated_armor.py`

---

#### 46. Coated Armor (card)

**Severity**: medium

**Description**: Claims to trigger on 'reduces incoming damage'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/coated_armor.py`

---

#### 47. Iron Guard (card)

**Severity**: medium

**Description**: Claims +10% DEF effect

**Observed Behavior**: Code implements 0.55 (55.0%) for def

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/iron_guard.py`

---

#### 48. Steel Bangles (card)

**Severity**: medium

**Description**: Claims to trigger on 'attack hit'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/steel_bangles.py`

---

#### 49. Guardian Shard (card)

**Severity**: medium

**Description**: Claims to trigger on 'for the next battle'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/guardian_shard.py`

---

#### 50. Polished Shield (card)

**Severity**: medium

**Description**: Claims to trigger on 'an ally resists a dot'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/polished_shield.py`

---

#### 51. Tactical Kit (card)

**Severity**: medium

**Description**: Claims 1% HP effect

**Observed Behavior**: Code implements 0.02 (2.0%) for hp

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/tactical_kit.py`

---

#### 52. Vital Core (card)

**Severity**: medium

**Description**: Claims 30% HP effect

**Observed Behavior**: Code implements 0.03 (3.0%) for hp

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/vital_core.py`

---

#### 53. Vital Core (card)

**Severity**: medium

**Description**: Claims to trigger on 'below 30'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/vital_core.py`

---

#### 54. Sharpening Stone (card)

**Severity**: medium

**Description**: Claims +2% crit effect

**Observed Behavior**: Code implements 0.03 (3.0%) for crit

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/sharpening_stone.py`

---

#### 55. Sharpening Stone (card)

**Severity**: medium

**Description**: Claims to trigger on 'scoring a crit'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/sharpening_stone.py`

---

#### 56. Calm Beads (card)

**Severity**: medium

**Description**: Claims to trigger on 'resisting a debuff'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/calm_beads.py`

---

#### 57. Enduring Will (card)

**Severity**: medium

**Description**: Claims +0.2% mitigation effect

**Observed Behavior**: Code implements 0.03 (3.0%) for mitigation

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/enduring_will.py`

---

#### 58. Enduring Will (card)

**Severity**: medium

**Description**: Claims to trigger on 'next battle'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/enduring_will.py`

---

#### 59. Thick Skin (card)

**Severity**: medium

**Description**: Claims to trigger on 'afflicted by bleed'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/thick_skin.py`

---

#### 60. Thick Skin (card)

**Severity**: medium

**Description**: Claims to trigger on 'by 1'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/thick_skin.py`

---

#### 61. Critical Overdrive (card)

**Severity**: high

**Description**: Claims +10% Crit effect

**Observed Behavior**: No crit effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/critical_overdrive.py`

---

#### 62. Critical Overdrive (card)

**Severity**: high

**Description**: Claims +2% Crit effect

**Observed Behavior**: No crit effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/critical_overdrive.py`

---

#### 63. Enduring Charm (card)

**Severity**: high

**Description**: Claims 30% HP effect

**Observed Behavior**: No hp effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/enduring_charm.py`

---

#### 64. Enduring Charm (card)

**Severity**: medium

**Description**: Claims to trigger on 'below 30'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/enduring_charm.py`

---

#### 65. Rejuvenating Tonic (card)

**Severity**: high

**Description**: Claims +1% HP effect

**Observed Behavior**: No hp effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/rejuvenating_tonic.py`

---

#### 66. Rejuvenating Tonic (card)

**Severity**: medium

**Description**: Claims to trigger on 'using a heal'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/rejuvenating_tonic.py`

---

#### 67. Micro Blade (card)

**Severity**: medium

**Description**: Claims to trigger on 'hit'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/a_micro_blade.py`

---

#### 68. Lightweight Boots (card)

**Severity**: high

**Description**: Claims 2% HP effect

**Observed Behavior**: No hp effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/lightweight_boots.py`

---

#### 69. Lightweight Boots (card)

**Severity**: medium

**Description**: Claims to trigger on 'successful dodge'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/lightweight_boots.py`

---

#### 70. Temporal Shield (card)

**Severity**: high

**Description**: Claims 99% damage effect

**Observed Behavior**: No damage effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/temporal_shield.py`

---

#### 71. Temporal Shield (card)

**Severity**: medium

**Description**: Claims to trigger on 'for that turn'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/temporal_shield.py`

---

#### 72. Temporal Shield (card)

**Severity**: high

**Description**: Claims to deal damage but no damage calculations found in code

**Observed Behavior**: No apply_damage calls found in implementation

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/temporal_shield.py`

---

#### 73. Balanced Diet (card)

**Severity**: medium

**Description**: Claims +2% DEF effect

**Observed Behavior**: Code implements 0.03 (3.0%) for def

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/balanced_diet.py`

---

#### 74. Balanced Diet (card)

**Severity**: medium

**Description**: Claims to trigger on 'healed'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/balanced_diet.py`

---

#### 75. Mystic Aegis (card)

**Severity**: medium

**Description**: Claims to trigger on 'an ally resists a debuff'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/mystic_aegis.py`

---

#### 76. Swift Footwork (card)

**Severity**: medium

**Description**: Claims to trigger on 'per turn'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/swift_footwork.py`

---

#### 77. Swift Footwork (card)

**Severity**: medium

**Description**: Claims to trigger on 'each combat is free'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/swift_footwork.py`

---

#### 78. Expert Manual (card)

**Severity**: medium

**Description**: Claims to trigger on 'a kill once per battle'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/expert_manual.py`

---

#### 79. Keen Goggles (card)

**Severity**: medium

**Description**: Claims +1% crit effect

**Observed Behavior**: Code implements 0.03 (3.0%) for crit

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/keen_goggles.py`

---

#### 80. Keen Goggles (card)

**Severity**: low

**Description**: Documentation mentions stacking but no stack-related code found

**Observed Behavior**: No stack-related methods or events found

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/keen_goggles.py`

---

#### 81. Sturdy Vest (card)

**Severity**: medium

**Description**: Claims 35% HP effect

**Observed Behavior**: Code implements 0.03 (3.0%) for hp

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/sturdy_vest.py`

---

#### 82. Sturdy Vest (card)

**Severity**: medium

**Description**: Claims to trigger on 'below 35'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/sturdy_vest.py`

---

#### 83. Precision Sights (card)

**Severity**: medium

**Description**: Claims +2% crit effect

**Observed Behavior**: Code implements 0.04 (4.0%) for crit

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/precision_sights.py`

---

#### 84. Precision Sights (card)

**Severity**: medium

**Description**: Claims to trigger on 'scoring a crit'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/precision_sights.py`

---

#### 85. Precision Sights (card)

**Severity**: low

**Description**: Documentation mentions stacking but no stack-related code found

**Observed Behavior**: No stack-related methods or events found

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/precision_sights.py`

---

#### 86. Critical Transfer (card)

**Severity**: high

**Description**: Claims +4% ATK effect

**Observed Behavior**: No atk effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/critical_transfer.py`

---

#### 87. Critical Transfer (card)

**Severity**: low

**Description**: Documentation mentions stacking but no stack-related code found

**Observed Behavior**: No stack-related methods or events found

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/critical_transfer.py`

---

#### 88. Reality Split (card)

**Severity**: high

**Description**: Claims +50% Crit effect

**Observed Behavior**: No crit effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/reality_split.py`

---

#### 89. Lucky Coin (card)

**Severity**: medium

**Description**: Claims to trigger on 'critical hit'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/lucky_coin.py`

---

#### 90. Steady Grip (card)

**Severity**: medium

**Description**: Claims +2% ATK effect

**Observed Behavior**: Code implements 0.03 (3.0%) for atk

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/steady_grip.py`

---

#### 91. Steady Grip (card)

**Severity**: medium

**Description**: Claims to trigger on 'applying a control effect'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/cards/steady_grip.py`

---

#### 92. Rusty Buckle (relic)

**Severity**: medium

**Description**: Claims to trigger on 'aftertaste as party hp drops'

**Observed Behavior**: No matching trigger found in code. Code triggers: ['turn_start', 'damage_taken', 'heal_received']

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/rusty_buckle.py`

---

#### 93. Rusty Buckle (relic)

**Severity**: low

**Description**: Documentation mentions stacking but no stack-related code found

**Observed Behavior**: No stack-related methods or events found

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/rusty_buckle.py`

---

#### 94. Essence of 6858 (relic)

**Severity**: medium

**Description**: Claims to trigger on 'the card pool is exhausted'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/fallback_essence.py`

---

#### 95. Essence of 6858 (relic)

**Severity**: medium

**Description**: Claims to trigger on 'one'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/fallback_essence.py`

---

#### 96. Essence of 6858 (relic)

**Severity**: medium

**Description**: Claims to trigger on 'transcends the need for material cards'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/fallback_essence.py`

---

#### 97. Shiny Pebble (relic)

**Severity**: medium

**Description**: Claims to trigger on 'burst on the first hit'

**Observed Behavior**: No matching trigger found in code. Code triggers: ['damage_taken', 'turn_start']

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/shiny_pebble.py`

---

#### 98. Shiny Pebble (relic)

**Severity**: medium

**Description**: Claims to trigger on 'the first time an ally is hit'

**Observed Behavior**: No matching trigger found in code. Code triggers: ['damage_taken', 'turn_start']

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/shiny_pebble.py`

---

#### 99. Ember Stone (relic)

**Severity**: high

**Description**: Claims 50% ATK effect

**Observed Behavior**: No atk effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/ember_stone.py`

---

#### 100. Ember Stone (relic)

**Severity**: high

**Description**: Claims 25% HP effect

**Observed Behavior**: No hp effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/ember_stone.py`

---

#### 101. Ember Stone (relic)

**Severity**: high

**Description**: Claims 50% ATK effect

**Observed Behavior**: No atk effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/ember_stone.py`

---

#### 102. Ember Stone (relic)

**Severity**: medium

**Description**: Claims to trigger on 'a low'

**Observed Behavior**: No matching trigger found in code. Code triggers: ['damage_taken']

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/ember_stone.py`

---

#### 103. Ember Stone (relic)

**Severity**: low

**Description**: Documentation mentions stacking but no stack-related code found

**Observed Behavior**: No stack-related methods or events found

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/ember_stone.py`

---

#### 104. Frost Sigil (relic)

**Severity**: high

**Description**: Claims 5% ATK effect

**Observed Behavior**: No atk effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/frost_sigil.py`

---

#### 105. Frost Sigil (relic)

**Severity**: high

**Description**: Claims 5% ATK effect

**Observed Behavior**: No atk effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/frost_sigil.py`

---

#### 106. Frost Sigil (relic)

**Severity**: low

**Description**: Documentation mentions stacking but no stack-related code found

**Observed Behavior**: No stack-related methods or events found

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/frost_sigil.py`

---

#### 107. Echo Bell (relic)

**Severity**: medium

**Description**: Claims to trigger on 'each battle repeats at 15'

**Observed Behavior**: No matching trigger found in code. Code triggers: ['battle_start', 'action_used', 'healing_used']

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/echo_bell.py`

---

#### 108. Echo Bell (relic)

**Severity**: medium

**Description**: Claims to trigger on 'each battle repeats at 15'

**Observed Behavior**: No matching trigger found in code. Code triggers: ['battle_start', 'action_used', 'healing_used']

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/echo_bell.py`

---

#### 109. Echo Bell (relic)

**Severity**: low

**Description**: Documentation mentions stacking but no stack-related code found

**Observed Behavior**: No stack-related methods or events found

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/echo_bell.py`

---

#### 110. Tattered Flag (relic)

**Severity**: high

**Description**: Claims +3% ATK effect

**Observed Behavior**: No atk effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/tattered_flag.py`

---

#### 111. Tattered Flag (relic)

**Severity**: high

**Description**: Claims +3% ATK effect

**Observed Behavior**: No atk effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/tattered_flag.py`

---

#### 112. Timekeeper's Hourglass (relic)

**Severity**: low

**Description**: Documentation mentions stacking but no stack-related code found

**Observed Behavior**: No stack-related methods or events found

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/timekeepers_hourglass.py`

---

#### 113. Pocket Manual (relic)

**Severity**: high

**Description**: Claims +3% damage effect

**Observed Behavior**: No damage effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/pocket_manual.py`

---

#### 114. Pocket Manual (relic)

**Severity**: high

**Description**: Claims +3% damage effect

**Observed Behavior**: No damage effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/pocket_manual.py`

---

#### 115. Pocket Manual (relic)

**Severity**: medium

**Description**: Claims to trigger on 'an additional aftertaste hit dealing'

**Observed Behavior**: No matching trigger found in code. Code triggers: ['hit_landed']

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/pocket_manual.py`

---

#### 116. Pocket Manual (relic)

**Severity**: high

**Description**: Claims to deal damage but no damage calculations found in code

**Observed Behavior**: No apply_damage calls found in implementation

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/pocket_manual.py`

---

#### 117. Killer Instinct (relic)

**Severity**: high

**Description**: Claims +75% ATK effect

**Observed Behavior**: No atk effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/killer_instinct.py`

---

#### 118. Killer Instinct (relic)

**Severity**: high

**Description**: Claims +75% ATK effect

**Observed Behavior**: No atk effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/killer_instinct.py`

---

#### 119. Threadbare Cloak (relic)

**Severity**: low

**Description**: Documentation mentions stacking but no stack-related code found

**Observed Behavior**: No stack-related methods or events found

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/threadbare_cloak.py`

---

#### 120. Arcane Flask (relic)

**Severity**: medium

**Description**: Claims to trigger on 'an ultimate'

**Observed Behavior**: No matching trigger found in code. Code triggers: ['ultimate_used']

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/arcane_flask.py`

---

#### 121. Arcane Flask (relic)

**Severity**: medium

**Description**: Claims to trigger on 'an ultimate'

**Observed Behavior**: No matching trigger found in code. Code triggers: ['ultimate_used']

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/arcane_flask.py`

---

#### 122. Arcane Flask (relic)

**Severity**: low

**Description**: Documentation mentions stacking but no stack-related code found

**Observed Behavior**: No stack-related methods or events found

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/arcane_flask.py`

---

#### 123. Soul Prism (relic)

**Severity**: high

**Description**: Claims 1% HP effect

**Observed Behavior**: No hp effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/soul_prism.py`

---

#### 124. Soul Prism (relic)

**Severity**: high

**Description**: Claims 1% HP effect

**Observed Behavior**: No hp effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/soul_prism.py`

---

#### 125. Guardian Charm (relic)

**Severity**: high

**Description**: Claims +20% DEF effect

**Observed Behavior**: No def effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/guardian_charm.py`

---

#### 126. Guardian Charm (relic)

**Severity**: high

**Description**: Claims +20% DEF effect

**Observed Behavior**: No def effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/guardian_charm.py`

---

#### 127. Guardian Charm (relic)

**Severity**: low

**Description**: Documentation mentions stacking but no stack-related code found

**Observed Behavior**: No stack-related methods or events found

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/guardian_charm.py`

---

#### 128. Bent Dagger (relic)

**Severity**: medium

**Description**: Claims +1% ATK effect

**Observed Behavior**: Code implements 0.03 (3.0%) for atk

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/bent_dagger.py`

---

#### 129. Bent Dagger (relic)

**Severity**: medium

**Description**: Claims +1% ATK effect

**Observed Behavior**: Code implements 0.03 (3.0%) for atk

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/bent_dagger.py`

---

#### 130. Herbal Charm (relic)

**Severity**: low

**Description**: Documentation mentions stacking but no stack-related code found

**Observed Behavior**: No stack-related methods or events found

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/herbal_charm.py`

---

#### 131. Echoing Drum (relic)

**Severity**: low

**Description**: Documentation mentions stacking but no stack-related code found

**Observed Behavior**: No stack-related methods or events found

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/echoing_drum.py`

---

#### 132. Stellar Compass (relic)

**Severity**: high

**Description**: Claims +1.5% ATK effect

**Observed Behavior**: No atk effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/stellar_compass.py`

---

#### 133. Stellar Compass (relic)

**Severity**: high

**Description**: Claims +1.5% ATK effect

**Observed Behavior**: No atk effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/stellar_compass.py`

---

#### 134. Traveler's Charm (relic)

**Severity**: high

**Description**: Claims +25% DEF effect

**Observed Behavior**: No def effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/travelers_charm.py`

---

#### 135. Traveler's Charm (relic)

**Severity**: high

**Description**: Claims +10% mitigation effect

**Observed Behavior**: No mitigation effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/travelers_charm.py`

---

#### 136. Traveler's Charm (relic)

**Severity**: high

**Description**: Claims +25% DEF effect

**Observed Behavior**: No def effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/travelers_charm.py`

---

#### 137. Traveler's Charm (relic)

**Severity**: high

**Description**: Claims +10% mitigation effect

**Observed Behavior**: No mitigation effect found in code

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/travelers_charm.py`

---

#### 138. Traveler's Charm (relic)

**Severity**: medium

**Description**: Claims to trigger on 'hit'

**Observed Behavior**: No matching trigger found in code. Code triggers: ['damage_taken', 'turn_start', 'turn_end']

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/travelers_charm.py`

---

#### 139. Traveler's Charm (relic)

**Severity**: medium

**Description**: Claims to trigger on 'hit'

**Observed Behavior**: No matching trigger found in code. Code triggers: ['damage_taken', 'turn_start', 'turn_end']

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/travelers_charm.py`

---

#### 140. Traveler's Charm (relic)

**Severity**: medium

**Description**: Claims to trigger on 'next turn per stack'

**Observed Behavior**: No matching trigger found in code. Code triggers: ['damage_taken', 'turn_start', 'turn_end']

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/travelers_charm.py`

---

#### 141. Traveler's Charm (relic)

**Severity**: medium

**Description**: Claims to trigger on 'next turn per stack'

**Observed Behavior**: No matching trigger found in code. Code triggers: ['damage_taken', 'turn_start', 'turn_end']

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/travelers_charm.py`

---

#### 142. Traveler's Charm (relic)

**Severity**: low

**Description**: Documentation mentions stacking but no stack-related code found

**Observed Behavior**: No stack-related methods or events found

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/relics/travelers_charm.py`

---

#### 143. Generic (ult)

**Severity**: medium

**Description**: Claims to trigger on 'consistent damage without
    side effects'

**Observed Behavior**: No matching trigger found in code. Code triggers: []

**File**: `/home/runner/work/Midori-AI-AutoFighter/Midori-AI-AutoFighter/backend/plugins/damage_types/generic.py`

---

## Test Coverage

The audit analyzed the following aspects for each ability:

- ✅ Stat effect claims vs implementation
- ✅ Trigger event claims vs code
- ✅ Damage/healing calculation presence
- ✅ Targeting logic claims
- ✅ Special mechanic claims (stacking, etc.)

## Limitations

This audit has the following limitations:

- Static analysis only - no runtime behavior testing
- Complex conditional logic may not be fully captured
- Dynamic method calls and runtime calculations not analyzed
- Integration between abilities not tested

## Next Steps

### Immediate Actions

- [ ] Review and prioritize identified issues
- [ ] Fix critical and high severity discrepancies
- [ ] Update documentation or code to resolve medium/low issues
- [ ] Add unit tests for abilities lacking test coverage
- [ ] Consider implementing ability behavior validation framework
- [ ] Document ability design patterns and standards

### Long-term Improvements

- [ ] Implement automated testing for all ability mechanics
- [ ] Create ability behavior specification format
- [ ] Add pre-commit hooks to validate ability implementations
- [ ] Develop integration tests for ability interactions

---

*Audit completed on 2024-12-19 using automated analysis*
*Requested by: lunamidori5*
