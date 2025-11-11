# Add Documentation Fields to Event Horizon Relic

## Objective

Add `full_about` and `summarized_about` fields to the Event Horizon relic plugin to support enhanced documentation and future AI integration.

## Background

The game is adding structured documentation fields to all cards and relics to enable:
- Better in-game tooltips and help text
- Future LLM-based features that need to understand relic mechanics
- Consistent documentation patterns across all plugins

The Event Horizon relic was recently implemented but still uses the old `about` field instead of the new standardized fields.

## Task Details

**File to modify:** `backend/plugins/relics/event_horizon.py`

**Changes required:**
1. Remove the existing `about` field
2. Add a `full_about` field to the relic class with a detailed description of the relic's mechanics
3. Add a `summarized_about` field to the relic class with a brief, concise description (1-2 sentences)

**Guidelines:**
- The `full_about` should explain all mechanics, triggers, stacking behavior, and interactions in detail
- The `summarized_about` should be suitable for quick reference in game UI
- Keep descriptions clear, accurate, and consistent with the content from the old `about` field
- Reference the current `about` field content for accuracy
- Note that relics can stack, so mention stacking behavior when relevant
- Follow the style and tone of other relic descriptions in the game

**Description Format Standards:**

- **`summarized_about`**: Use qualitative descriptions WITHOUT specific numbers or percentages
  - Focus on the general effect type, not exact values
  - Use phrases like "boosts atk", "lowers def", "adds some hp", "reduces damage"
  - Example: "Boosts atk" instead of "Boosts atk by 500%"
  - Example: "Lowers def" instead of "Reduces def by 20%"
  - Example: "Grants shield based on max hp" instead of "Grants shield equal to 20% max HP"
  
- **`full_about`**: Include ALL specific numbers, percentages, and exact values
  - Explain all mechanics with precise details
  - Include exact values like "+500% ATK", "20% Max HP", "2 turns", "10% damage reduction", etc.
  - Example: "+500% ATK & +500% Effect Hit Rate; at the start of each battle, all allies gain +200% SPD for 2 turns"
  - Example: "+4% HP; if lethal damage would reduce you below 1 HP, reduce that damage by 10%"
  - Example: "After an Ultimate, grant a shield equal to 20% Max HP per stack"

## Current About Field Content

```python
about: str = (
    "Detonates a gravity pulse at the start of every ally turn. Each pulse rips "
    "6% of current HP (minimum 1) from every living foe per stack, while draining "
    "the acting ally for 3% of their Max HP per stack. An all-or-nothing tempo engine."
)
```

## Example Structure

```python
@dataclass
class EventHorizon(RelicBase):
    id: str = "event_horizon"
    name: str = "Event Horizon"
    # ... existing fields ...
    # about field removed - replaced with full_about and summarized_about
    full_about: str = "Detailed description explaining all mechanics, stacking..."
    summarized_about: str = "Brief summary for UI"
```

## Acceptance Criteria

- [x] Old `about` field removed
- [x] `full_about` field added with comprehensive description including:
  - 6% of current HP damage per stack (minimum 1)
  - 3% of Max HP self-drain per stack
  - Trigger: start of every ally turn
  - Target: every living foe
- [x] `summarized_about` field added with concise description (no numbers)
- [x] Both descriptions are accurate to the relic's actual mechanics
- [x] Stacking behavior is mentioned if applicable
- [x] Code follows existing style and conventions
- [x] Changes are tested (relic still loads and functions correctly)

---

## Implementation Summary

**Implemented by:** Coder Mode Agent  
**Date:** 2025-11-11

### Changes Made
- Updated `backend/plugins/relics/event_horizon.py` (lines 19-26)
  - Removed old `about` field
  - Added `full_about` field with complete mechanics description (preserves original content)
  - Added `summarized_about` field: "Damages foes and drains acting ally each ally turn"

### Verification Results
- ✅ Linting: `ruff check` passes with no issues
- ✅ All 9 existing tests pass:
  - `test_event_horizon_basic_pulse`
  - `test_event_horizon_multiple_stacks`
  - `test_event_horizon_minimum_damage`
  - `test_event_horizon_no_living_foes`
  - `test_event_horizon_foe_turns_ignored`
  - `test_event_horizon_extra_turns`
  - `test_event_horizon_battle_end_cleanup`
  - `test_event_horizon_ally_no_hp`
  - `test_event_horizon_describe`
- ✅ Relic loads and instantiates correctly
- ✅ New fields properly formatted according to standards

---

## Audit Summary (Auditor Mode - 2025-11-11)

**Audited by:** Auditor Mode Agent  
**Status:** ✅ APPROVED - All acceptance criteria met

### Verification Results

#### ✅ Implementation (`backend/plugins/relics/event_horizon.py`)
- Lines 19-23: `full_about` field with comprehensive description
  - ✅ Includes 6% current HP damage per stack (minimum 1)
  - ✅ Includes 3% Max HP self-drain per stack
  - ✅ Includes trigger: "start of every ally turn"
  - ✅ Includes target: "every living foe"
  - ✅ Mentions stacking: "per stack" appears multiple times
  - ✅ Preserves original content and context
- Lines 24-26: `summarized_about` field with brief description
  - ✅ No specific numbers or percentages
  - ✅ Qualitative description: "Damages foes and drains acting ally"
  - ✅ Suitable for UI quick reference
- ✅ Old `about` field completely removed

#### ✅ Tests (`backend/tests/test_event_horizon.py`)
All 9 tests passing:
- `test_event_horizon_basic_pulse`: ✅ PASS
- `test_event_horizon_multiple_stacks`: ✅ PASS
- `test_event_horizon_minimum_damage`: ✅ PASS
- `test_event_horizon_no_living_foes`: ✅ PASS
- `test_event_horizon_foe_turns_ignored`: ✅ PASS
- `test_event_horizon_extra_turns`: ✅ PASS
- `test_event_horizon_battle_end_cleanup`: ✅ PASS
- `test_event_horizon_ally_no_hp`: ✅ PASS
- `test_event_horizon_describe`: ✅ PASS

#### ✅ Code Quality
- Linting: `ruff check` passes with no issues
- Style: Follows repository conventions
- Import verification: Relic instantiates correctly with new fields

### Requirements Checklist
- [x] Old `about` field removed
- [x] `full_about` field added with all required details
- [x] `summarized_about` field added without numbers
- [x] Both descriptions accurate to mechanics
- [x] Stacking behavior mentioned
- [x] Code follows style conventions
- [x] All tests passing (9/9)
- [x] Linting clean

**Recommendation:** This task is complete and ready for Task Master review and closure. This completes the card/relic documentation migration project (now at 100% - 42/42 relics and 62/62 cards migrated).

requesting review from the Task Master
