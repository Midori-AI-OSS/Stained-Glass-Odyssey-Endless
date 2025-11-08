# Add Documentation Fields to Overclock Card

## Objective

Add `full_about` and `summarized_about` fields to the Overclock card plugin to support enhanced documentation and future AI integration.

## Background

The game is adding structured documentation fields to all cards and relics to enable:
- Better in-game tooltips and help text
- Future LLM-based features that need to understand card mechanics
- Consistent documentation patterns across all plugins

## Task Details

**File to modify:** `backend/plugins/cards/overclock.py`

**Changes required:**
1. Remove the existing `about` field
2. Add a `full_about` field to the card class with a detailed description of the card's mechanics
3. Add a `summarized_about` field to the card class with a brief, concise description (1-2 sentences)

**Guidelines:**
- The `full_about` should explain all mechanics, triggers, and interactions in detail
- The `summarized_about` should be suitable for quick reference in game UI
- Keep descriptions clear, accurate, and consistent with the content from the old `about` field
- Reference the current `about` field content for accuracy
- Follow the style and tone of other card descriptions in the game
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

## Example Structure

```python
@dataclass
class OverclockCard(CardBase):
    id: str = "overclock"
    name: str = "Overclock"
    # ... existing fields ...
    # about field removed - replaced with full_about and summarized_about
    full_about: str = "Detailed description explaining all mechanics..."
    summarized_about: str = "Brief summary for UI"
```

## Acceptance Criteria

- [x] Old `about` field removed
- [x] `full_about` field added with comprehensive description
- [x] `summarized_about` field added with concise description
- [x] Both descriptions are accurate to the card's actual mechanics
- [x] Code follows existing style and conventions
- [x] Changes are tested (card still loads and functions correctly)

## Audit Summary (Auditor Mode - 2025-11-08 Updated)

**Audited by:** GitHub Copilot Agent  
**Audit Date:** 2025-11-07 (verified 2025-11-08)  
**Result:** ✅ PASSED

**Verification Performed:**
- Confirmed `about` field removed from backend/plugins/cards/overclock.py
- Verified `full_about` field present with detailed mechanics description including all specific values (+500% ATK, +500% Effect Hit Rate, +200% SPD, 2 turns)
- Verified `summarized_about` field present with qualitative description (no specific numbers)
- Cross-referenced descriptions against actual code implementation:
  - effects dict: {"atk": 5, "effect_hit_rate": 5} = 500% multipliers ✓
  - _grant_speed_boost function: spd_mult=3.0 (200% increase), turns=2 ✓
  - Applied to all allies at battle_start event ✓
- Description format standards followed correctly
- Code style and conventions maintained
- All acceptance criteria accurately marked as complete
- Linting passes (`ruff check` clean)

**Conclusion:** Implementation is correct and complete. No issues found.

requesting review from the Task Master
