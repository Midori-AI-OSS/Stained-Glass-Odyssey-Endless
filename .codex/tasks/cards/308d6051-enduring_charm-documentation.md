# Add Documentation Fields to Enduring Charm Card

## Objective

Add `full_about` and `summarized_about` fields to the Enduring Charm card plugin to support enhanced documentation and future AI integration.

## Background

The game is adding structured documentation fields to all cards and relics to enable:
- Better in-game tooltips and help text
- Future LLM-based features that need to understand card mechanics
- Consistent documentation patterns across all plugins

## Task Details

**File to modify:** `backend/plugins/cards/enduring_charm.py`

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
class EnduringCharmCard(CardBase):
    id: str = "enduring_charm"
    name: str = "Enduring Charm"
    # ... existing fields ...
    # about field removed - replaced with full_about and summarized_about
    full_about: str = "Detailed description explaining all mechanics..."
    summarized_about: str = "Brief summary for UI"
```

## Acceptance Criteria

- [ ] Old `about` field removed
- [ ] `full_about` field added with comprehensive description
- [ ] `summarized_about` field added with concise description
- [ ] Both descriptions are accurate to the card's actual mechanics
- [ ] Code follows existing style and conventions
- [ ] Changes are tested (card still loads and functions correctly)


## Audit Notes (2025-11-03)
✅ All acceptance criteria met
✅ Linting passes
✅ `summarized_about` uses qualitative descriptions (no specific numbers)
✅ `full_about` includes all specific mechanics (+3% Vitality, 30% HP threshold, +3% Vitality bonus, 2 turns)
✅ Descriptions accurately match code implementation (lines 14-18, 39, 56)

requesting review from the Task Master
