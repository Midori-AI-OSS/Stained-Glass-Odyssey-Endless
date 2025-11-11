# Add Documentation Fields to Mindful Tassel Card

## Objective

Add `full_about` and `summarized_about` fields to the Mindful Tassel card plugin to support enhanced documentation and future AI integration.

## Background

The game is adding structured documentation fields to all cards and relics to enable:
- Better in-game tooltips and help text
- Future LLM-based features that need to understand card mechanics
- Consistent documentation patterns across all plugins

## Task Details

**File to modify:** `backend/plugins/cards/mindful_tassel.py`

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
class MindfulTasselCard(CardBase):
    id: str = "mindful_tassel"
    name: str = "Mindful Tassel"
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

---

## Audit Results (2025-11-11)

**Auditor:** AI Agent (Auditor Mode)  
**Status:** ✅ APPROVED

### Verification Performed:

1. ✅ **Code Review**: All acceptance criteria verified
   - No `about` field present (correctly removed)
   - `full_about` present: "+3% Effect Hit Rate; the first debuff applied each battle has +5% potency (increased damage or duration)."
   - `summarized_about` present: "Boosts effect hit rate; first debuff each battle gains potency"
   
2. ✅ **Accuracy Check**: Verified descriptions match implementation
   - Effect Hit Rate: +3% (line 15) ✓
   - First debuff: +5% potency to damage (line 66) or duration (line 69) ✓
   - Only applies once per battle (bonus_used flag) ✓
   
3. ✅ **Format Compliance**: Verified description format standards
   - `summarized_about` has NO numbers/percentages (qualitative only) ✓
   - `full_about` includes specific values (+3%, +5%) ✓

### Recommendation:
Implementation is complete and accurate. All acceptance criteria met.

requesting review from the Task Master
