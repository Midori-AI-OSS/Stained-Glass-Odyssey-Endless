# Add Documentation Fields to Eclipse Reactor Relic

## Objective

Add `full_about` and `summarized_about` fields to the Eclipse Reactor relic plugin to support enhanced documentation and future AI integration.

## Background

The game is adding structured documentation fields to all cards and relics to enable:
- Better in-game tooltips and help text
- Future LLM-based features that need to understand relic mechanics
- Consistent documentation patterns across all plugins

## Task Details

**File to modify:** `backend/plugins/relics/eclipse_reactor.py`

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
class EclipseReactorRelic(RelicBase):
    id: str = "eclipse_reactor"
    name: str = "Eclipse Reactor"
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

## Audit Notes (2025-11-07)
✅ All acceptance criteria met
✅ Linting passes
✅ `summarized_about` uses qualitative descriptions (no specific numbers)
✅ `full_about` includes all specific mechanics (18% drain, +180% ATK/SPD, +60% crit dmg, 3 turns, 2% bleed)
✅ Stacking behavior properly documented (per stack scaling)
✅ Descriptions accurately match code implementation (lines 78, 94, 120-126, 192)
✅ `full_about_stacks()` method implemented (lines 243-245)
✅ `describe()` method provides stack-specific details (lines 231-241)

ready for review
