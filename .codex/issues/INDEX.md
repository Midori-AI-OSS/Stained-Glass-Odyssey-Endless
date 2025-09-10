# Gameplay Entity Audit Issue Index

**Generated**: Comprehensive Code Audit  
**Scope**: Ultimates, Passives, Characters, Cards, Relics  
**Total Issues Found**: 6 active issues, 1 resolved  

## Critical Issues (Game-Breaking)

### CRITICAL-001: Lady Echo Lightning Ultimate Crash ✅ FIXED
- **Entity**: Lady Echo (Lightning damage type)
- **Impact**: Complete character unusability, runtime crashes
- **Status**: Fixed in commit a222b5c
- **File**: `.codex/issues/CRITICAL-001-lady-echo-lightning-ultimate-crash.issue`

## High Severity Issues (Major Gameplay Impact)

### HIGH-001: Eight Characters Have Random Ultimates 🔴 ACTIVE
- **Entities**: Ally, Becca, Bubbles, Ixia, Graygray, Hilander, Mezzy, Mimic
- **Impact**: Unpredictable character behavior, breaks game balance
- **Root Cause**: Fallback to `random_damage_type()` in damage type resolution
- **File**: `.codex/issues/HIGH-001-eight-characters-random-ultimates.issue`

## Medium Severity Issues (Moderate Impact)

### MEDIUM-001: Lady Fire and Ice Inconsistent Ultimate 🟡 ACTIVE
- **Entity**: Lady Fire and Ice
- **Impact**: Character gets either Fire OR Ice ultimate randomly
- **Root Cause**: Dual substring matching in damage type resolution
- **File**: `.codex/issues/MEDIUM-001-lady-fire-ice-inconsistent-ultimate.issue`

### MEDIUM-002: Missing Gacha Rarity Fields 🟡 ACTIVE
- **Entities**: Luna, Lady of Fire
- **Impact**: Potential gacha system issues, field inconsistency
- **File**: `.codex/issues/MEDIUM-002-missing-gacha-rarity-fields.issue`

### MEDIUM-003: Arc Lightning ATK Percentage Verification ✅ NO ISSUE
- **Entity**: Arc Lightning (card)
- **Status**: Verified correct - implementation matches description
- **File**: `.codex/issues/MEDIUM-003-arc-lightning-percentage-verification.issue`

### MEDIUM-004: Adamantine Band Lethal Protection Implementation Issue 🟡 ACTIVE
- **Entity**: Adamantine Band (card)
- **Impact**: Damage reduction may not work correctly due to timing issues
- **Root Cause**: Post-damage HP restoration instead of damage prevention
- **File**: `.codex/issues/MEDIUM-004-adamantine-band-lethal-protection-issue.issue`

## Low Severity Issues (Maintenance/Cleanup)

### LOW-001: Orphaned Passive Implementations 🔵 ACTIVE
- **Entities**: advanced_combat_synergy, room_heal (passives)
- **Impact**: Dead code, maintenance burden
- **File**: `.codex/issues/LOW-001-orphaned-passive-implementations.issue`

## Audit Coverage Summary

### ✅ Fully Audited
- **Characters (18)**: All characters and their ultimate/passive assignments reviewed
- **Damage Types (8)**: All ultimate implementations verified
- **Passives (21)**: All passive assignments and orphaned passives identified

### 🔍 Sample Audited  
- **Cards (~50)**: Representative sample reviewed, one potential issue identified
- **Relics (~28)**: Sample reviewed, no major issues in sample

### 📋 Audit Methodology
1. **Discovery**: Systematic entity inventory and classification
2. **Verification**: Cross-reference claimed vs implemented behavior  
3. **Documentation**: Structured .issue files with reproduction steps
4. **Prioritization**: Severity-based classification (Critical → Low)

## Resolution Priority

### Immediate Action Required
1. **HIGH-001**: Fix random ultimate assignment for 8 characters
2. **MEDIUM-004**: Investigate Adamantine Band damage reduction timing

### Investigation Required  
1. **MEDIUM-001**: Decide on Lady Fire and Ice ultimate behavior
2. **MEDIUM-002**: Verify gacha system requirements for missing fields

### Maintenance Tasks
1. **LOW-001**: Decide fate of orphaned passives (assign or remove)

## Related Documentation
- Original audit findings: `.codex/audit/17001dd5-*.audit.md`
- Character fix task: `.codex/tasks/3ab2622d-fix-lightning-ultimate-critical-bug.md`