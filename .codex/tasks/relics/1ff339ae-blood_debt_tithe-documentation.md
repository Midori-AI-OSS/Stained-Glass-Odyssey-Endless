# Add Documentation Fields to Blood Debt Tithe Relic

## Objective

Add `full_about` and `summarized_about` fields to the Blood Debt Tithe relic plugin to support enhanced documentation and future AI integration.

## Background

The game is adding structured documentation fields to all cards and relics to enable:
- Better in-game tooltips and help text
- Future LLM-based features that need to understand relic mechanics
- Consistent documentation patterns across all plugins

## Task Details

**File to modify:** `backend/plugins/relics/blood_debt_tithe.py`

**Changes required:**
1. Remove the existing `about` field
2. Add a `full_about` field to the relic class with a detailed description of the relic's mechanics
3. Add a `summarized_about` field to the relic class with a brief, concise description (1-2 sentences)

**Guidelines:**
- The `full_about` should explain all mechanics, triggers, stacking behavior, and interactions in detail
- The `summarized_about` should be suitable for quick reference in game UI
- Keep descriptions clear, accurate, and consistent with the content from the old `about` field
- Reference the current `about` field content and `describe()` method for accuracy
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

## Example Structure

```python
@dataclass
class BloodDebtTitheRelic(RelicBase):
    id: str = "blood_debt_tithe"
    name: str = "Blood Debt Tithe"
    # ... existing fields ...
    # about field removed - replaced with full_about and summarized_about
    full_about: str = "Detailed description explaining all mechanics, stacking..."
    summarized_about: str = "Brief summary for UI"
```

## Acceptance Criteria

- [x] Old `about` field removed
- [x] `full_about` field added with comprehensive description
- [x] `summarized_about` field added with concise description
- [x] Both descriptions are accurate to the relic's actual mechanics
- [x] Stacking behavior is mentioned if applicable
- [x] Code follows existing style and conventions
- [x] Changes are tested (relic still loads and functions correctly)

## Audit Summary (2025-11-03)

**Status: APPROVED**

Audited by reviewing `backend/plugins/relics/blood_debt_tithe.py`. All acceptance criteria met:
- ✓ Old `about` field removed (confirmed absent)
- ✓ `full_about` properly implemented: "Every defeated foe increases the party's rare drop rate for the rest of the run. Future encounters begin with foes empowered proportionally to the number of sacrifices already collected (+3% ATK and +2% SPD per stored defeat per stack)."
- ✓ `summarized_about` properly implemented: "Defeated foes grant rare drop rate; future foes are empowered based on defeats"
- ✓ Description format standards followed (summarized has no numbers, full has "+3%", "+2%")
- ✓ Descriptions accurate to defeat tracking and foe buffing mechanics
- ✓ Stacking behavior properly documented and implemented
- ✓ Code style consistent with repository conventions
- ✓ Proper `full_about_stacks()` and `describe()` methods implemented
- ✓ Complex persistent state tracking across battles

This is a sophisticated 4-star relic with excellent implementation of run-persistent mechanics.

Requesting review from the Task Master.
