# Add Documentation Fields to Eclipse Theater Sigil Card

## Objective

Add `full_about` and `summarized_about` fields to the Eclipse Theater Sigil card plugin to support enhanced documentation and future AI integration.

## Background

The game is adding structured documentation fields to all cards and relics to enable:
- Better in-game tooltips and help text
- Future LLM-based features that need to understand card mechanics
- Consistent documentation patterns across all plugins

## Task Details

**File to modify:** `backend/plugins/cards/eclipse_theater_sigil.py`

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
class EclipseTheaterSigilCard(CardBase):
    id: str = "eclipse_theater_sigil"
    name: str = "Eclipse Theater Sigil"
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

## Audit Summary (2025-11-03)

**Status: APPROVED**

Audited by reviewing `backend/plugins/cards/eclipse_theater_sigil.py`. All acceptance criteria met:
- ✓ Old `about` field removed (confirmed absent)
- ✓ `full_about` properly implemented: "+1500% Max HP & ATK. Alternates Light/Dark each turn: Light cleanses one DoT per ally and grants 2-turn Radiant Regeneration, Dark inflicts Abyssal Weakness on foes and gives allies a one-action +50% crit burst."
- ✓ `summarized_about` properly implemented: "Massively boosts hp and atk; alternates Light and Dark effects each turn"
- ✓ Description format standards followed (summarized has no numbers, full has all specific values)
- ✓ Descriptions accurate to complex Light/Dark rotation mechanics
- ✓ Code style consistent with repository conventions

This is a high-quality 5-star card with sophisticated implementation.

Requesting review from the Task Master.
